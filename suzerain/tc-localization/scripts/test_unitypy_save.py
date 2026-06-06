# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "UnityPy>=1.20",
# ]
# ///
"""Test if UnityPy save_typetree actually works."""

import UnityPy
from pathlib import Path
import tempfile

orig_path = Path("backup/20260530-full-original/scenes_scenes_assets_scenes_mainmenu.unity_6dd6ca6b71e2733b13cf2860d4a95134.bundle")
with open(orig_path, 'rb') as f:
    orig_data = f.read()

print(f"Original file: {len(orig_data)} bytes")

# Test 1: Save without modifications
env = UnityPy.load(str(orig_path))
saved_no_mod = env.file.save(packer="lz4")
print(f"Saved (no mods): {len(saved_no_mod)} bytes")

# Test 2: Make a single patch
env2 = UnityPy.load(str(orig_path))
TMP_TEXT_SCRIPT = 7477354737935883349
patched = 0

for obj in env2.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    try:
        tree = obj.read_typetree()
    except:
        continue
    script = tree.get("m_Script")
    if not isinstance(script, dict) or script.get("m_PathID") != TMP_TEXT_SCRIPT:
        continue
    src = tree.get("m_text")
    if isinstance(src, str) and src == "LOAD":
        print(f"Found LOAD, patching to 載入...")
        tree["m_text"] = "載入"
        obj.save_typetree(tree)
        patched += 1
        break

print(f"Made {patched} patches")

with tempfile.NamedTemporaryFile(suffix=".bundle", delete=False) as tmp:
    tmp_path = Path(tmp.name)
    saved_with_mod = env2.file.save(packer="lz4")
    tmp_path.write_bytes(saved_with_mod)
    print(f"Saved (with mods): {len(saved_with_mod)} bytes")
    print(f"Temp file: {tmp_path}")

# Test 3: Verify patch persisted
print(f"\nVerifying patch in saved bundle...")
env3 = UnityPy.load(str(tmp_path))
found_patch = False

for obj in env3.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    try:
        tree = obj.read_typetree()
        m_text = tree.get("m_text")
        if m_text == "載入":
            print(f"✓ PATCH PERSISTED: Found '載入'")
            found_patch = True
            break
        elif m_text == "LOAD":
            print(f"✗ PATCH FAILED: Still says 'LOAD'")
            break
    except:
        pass

if not found_patch:
    print(f"Could not find either LOAD or 載入 in reloaded bundle - data corrupt?")

print(f"\nFile size comparison:")
print(f"  Original:        {len(orig_data):,} bytes")
print(f"  Resaved (no mod): {len(saved_no_mod):,} bytes")
print(f"  Resaved (patched):{len(saved_with_mod):,} bytes")
