#!/usr/bin/env python3
"""Decode DoW DE .rgd files into the AttributeEditor-style Lua representation.

The .rgd (Relic Chunky + AEGD) format:
  AEGD = u32 root_hash | u32 data_size | TABLE
  TABLE = u32 count | count * ENTRY | VALUES
  ENTRY = u32 key_hash | u32 value_type | u32 offset  (offset relative to VALUES start)
  value_type: 0=f32, 2=int16, 3=string(path), 4=u32, 100=table/list

Key hashes use Bob Jenkins' 1996 evahash (a=b=0x9e3779b9, c=initval, mix()).
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

MASK = 0xFFFFFFFF


def _rot(x: int, k: int) -> int:
    return ((x << k) | (x >> (32 - k))) & MASK


def _mix(a: int, b: int, c: int):
    a = (a - b) & MASK
    a = (a - c) & MASK
    a ^= c >> 13
    b = (b - c) & MASK
    b = (b - a) & MASK
    b ^= (a << 8) & MASK
    c = (c - a) & MASK
    c = (c - b) & MASK
    c ^= b >> 13
    a = (a - b) & MASK
    a = (a - c) & MASK
    a ^= c >> 12
    b = (b - c) & MASK
    b = (b - a) & MASK
    b ^= (a << 16) & MASK
    c = (c - a) & MASK
    c = (c - b) & MASK
    c ^= b >> 5
    a = (a - b) & MASK
    a = (a - c) & MASK
    a ^= c >> 3
    b = (b - c) & MASK
    b = (b - a) & MASK
    b ^= (a << 10) & MASK
    c = (c - a) & MASK
    c = (c - b) & MASK
    c ^= b >> 15
    return a & MASK, b & MASK, c & MASK


def relic_hash(key: bytes | str, initval: int = 0) -> int:
    k = key if isinstance(key, bytes) else key.encode("latin1")
    length = len(k)
    a = b = 0x9E3779B9
    c = initval
    i = 0
    while length >= 12:
        a += k[i] + (k[i + 1] << 8) + (k[i + 2] << 16) + (k[i + 3] << 24)
        b += k[i + 4] + (k[i + 5] << 8) + (k[i + 6] << 16) + (k[i + 7] << 24)
        c += k[i + 8] + (k[i + 9] << 8) + (k[i + 10] << 16) + (k[i + 11] << 24)
        a &= MASK
        b &= MASK
        c &= MASK
        a, b, c = _mix(a, b, c)
        i += 12
        length -= 12
    c += len(k)
    k = k[i:]
    L = len(k)
    if L >= 11:
        c += k[10] << 24
    if L >= 10:
        c += k[9] << 16
    if L >= 9:
        c += k[8] << 8
    if L >= 8:
        b += k[7] << 24
    if L >= 7:
        b += k[6] << 16
    if L >= 6:
        b += k[5] << 8
    if L >= 5:
        b += k[4]
    if L >= 4:
        a += k[3] << 24
    if L >= 3:
        a += k[2] << 16
    if L >= 2:
        a += k[1] << 8
    if L >= 1:
        a += k[0]
    a &= MASK
    b &= MASK
    c &= MASK
    a, b, c = _mix(a, b, c)
    return c


def extract_aegd(path: str | Path) -> bytes:
    data = Path(path).read_bytes()
    # Relic Chunky header: 16-byte magic + version + chunk_count
    magic = b"Relic Chunky\r\n\x1a\x00"
    assert data[:16] == magic, data[:20]
    off = 16
    version, chunk_count = struct.unpack_from("<II", data, off)
    off += 8
    for _ in range(chunk_count):
        ctype = data[off:off + 8]
        ver, size = struct.unpack_from("<II", data, off + 8)
        off += 16
        if ctype == b"DATAAEGD":
            return data[off:off + size]
        off += size
    raise ValueError("no DATAAEGD chunk")


class Decoder:
    def __init__(self, aegd: bytes):
        self.rb = aegd
        # AEGD header: u32 unknown(0) | u32 root_hash | u32 data_size | u32 count
        self.unknown, self.root_hash, self.data_size, self.count = struct.unpack_from("<IIII", aegd, 0)
        self.data_start = 16 + self.count * 12

    def _table(self, abs_table: int):
        if abs_table < 0 or abs_table + 4 > len(self.rb):
            return None
        count = struct.unpack_from("<I", self.rb, abs_table)[0]
        if count > 200000 or abs_table + 4 + count * 12 > len(self.rb) + 64:
            return None
        vals_start = abs_table + 4 + count * 12
        entries = []
        for i in range(count):
            eo = abs_table + 4 + i * 12
            kh, typ, off = struct.unpack_from("<III", self.rb, eo)
            entries.append((kh, typ, vals_start + off))
        return count, entries, vals_start

    def _read_cstr(self, abs_off: int, maxlen: int = 300) -> str:
        end = self.rb.find(b"\x00", abs_off, abs_off + maxlen)
        if end < 0:
            end = abs_off + maxlen
        return self.rb[abs_off:end].decode("latin1", "replace")

    def _read_ucs(self, abs_off: int, maxlen: int = 64) -> str:
        raw = self.rb[abs_off:abs_off + maxlen]
        end = raw.find(b"\x00\x00")
        if end >= 0:
            raw = raw[:end]
        if len(raw) % 2:
            raw = raw[:-1]
        return raw.decode("utf-16-le", "replace")

    def _value(self, typ: int, vabs: int):
        if typ == 0:
            return struct.unpack_from("<f", self.rb, vabs)[0]
        if typ == 2:
            return struct.unpack_from("<h", self.rb, vabs)[0]
        if typ == 3:
            return self._read_cstr(vabs)
        if typ == 4:
            return struct.unpack_from("<I", self.rb, vabs)[0]
        if typ == 100:
            return ("TABLE", vabs)
        return (f"t{typ}", vabs)

    def decode(self, abs_table: int | None = None, name: str = "data"):
        if abs_table is None:
            abs_table = self.data_start
        return self._node(abs_table)

    def _node(self, abs_table: int):
        t = self._table(abs_table)
        if t is None:
            return None
        count, entries, vals_start = t
        out = []
        for kh, typ, vabs in entries:
            key = hex(kh) if kh >= 0 else hex(kh)
            if typ == 100:
                sub = self._table(vabs)
                if sub is not None:
                    val = self._node(vabs)
                    out.append((key, val))
                else:
                    out.append((key, ("table?", vabs)))
            else:
                out.append((key, self._value(typ, vabs)))
        return out

    def to_lua(self, name: str = "GameData") -> str:
        node = self._node(self.data_start)
        lines = [f"{name} = Inherit([[{{file}}]])"]
        self._emit(node, lines, [name])
        return "\n".join(lines)

    def _emit(self, node, lines, stack):
        for key, val in node:
            if isinstance(val, list):
                lines.append(f'{self._path(stack)}["{key}"] = {{')
                self._emit(val, lines, [])
                lines.append("}")
            else:
                pass


def dump_human(root: Decoder, indent: str = "", abs_table: int | None = None):
    t = root._table(abs_table if abs_table is not None else 12)
    if t is None:
        return
    count, entries, vals_start = t
    for kh, typ, vabs in entries:
        name = NAME_MAP.get(kh, hex(kh))
        if typ == 100:
            sub = root._table(vabs)
            if sub is not None:
                print(f"{indent}{name} (table[{sub[0]}]):")
                dump_human(root, indent + "  ", vabs)
            else:
                print(f"{indent}{name} (table?)")
        elif typ == 3:
            print(f'{indent}{name} = path "{root._read_cstr(vabs)}"')
        elif typ == 0:
            print(f"{indent}{name} = f32 {root._value(typ, vabs)}")
        elif typ == 2:
            print(f"{indent}{name} = int16 {root._value(typ, vabs)}")
        elif typ == 4:
            print(f"{indent}{name} = u32 {root._value(typ, vabs)}")
        else:
            print(f"{indent}{name} = ?{typ}")


NAME_MAP = {
    relic_hash("type"): "type",
    relic_hash("base_squad_cap"): "base_squad_cap",
    relic_hash("max_squad_cap"): "max_squad_cap",
    relic_hash("base_support_cap"): "base_support_cap",
    relic_hash("max_support_cap"): "max_support_cap",
    relic_hash("income_cap"): "income_cap",
    relic_hash("structure_name"): "structure_name",
    relic_hash("count"): "count",
    relic_hash("addon_name"): "addon_name",
    relic_hash("squad_name"): "squad_name",
    relic_hash("min_count"): "min_count",
    relic_hash("max_cumulative_squad_cap"): "max_cumulative_squad_cap",
    relic_hash("possible_research"): "possible_research",
    relic_hash("research_name"): "research_name",
    relic_hash("squad_activated"): "squad_activated",
    relic_hash("value_required"): "value_required",
    relic_hash("mobvalue_required"): "mobvalue_required",
    relic_hash("squad_requirement_ext"): "squad_requirement_ext",
    relic_hash("squad_cap_ext"): "squad_cap_ext",
    relic_hash("requirements"): "requirements",
    relic_hash("race_squad_cap_table"): "race_squad_cap_table",
    relic_hash("race_details"): "race_details",
    relic_hash("spawner_ext"): "spawner_ext",
    relic_hash("squad_table"): "squad_table",
    relic_hash("position"): "position",
    relic_hash("starting_res_normal"): "starting_res_normal",
    relic_hash("starting_res_quickstart"): "starting_res_quickstart",
    relic_hash("cost_ext"): "cost_ext",
    relic_hash("resource_ext"): "resource_ext",
    relic_hash("hq_ext"): "hq_ext",
    relic_hash("requisition_cost"): "requisition_cost",
    relic_hash("power_cost"): "power_cost",
    relic_hash("time_cost"): "time_cost",
    relic_hash("requisition_per_second"): "requisition_per_second",
    relic_hash("power_per_second"): "power_per_second",
    relic_hash("decay_enabled"): "decay_enabled",
    relic_hash("faith_per_second"): "faith_per_second",
    relic_hash("souls_per_second"): "souls_per_second",
    relic_hash("population_required"): "population_required",
    relic_hash("structure_name_exclusive"): "structure_name_exclusive",
    relic_hash("research_name_either"): "research_name_either",
}



if __name__ == "__main__":
    for path in sys.argv[1:]:
        print(f"===== {path} =====")
        aegd = extract_aegd(path)
        d = Decoder(aegd)
        dump_human(d)
