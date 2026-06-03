# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "UnityPy>=1.20",
# ]
# ///
"""Comprehensive audit of entity bundle for untranslated character/org content."""

import json
from pathlib import Path
from collections import defaultdict
import UnityPy

def is_english_like(s):
    """Check if string is primarily English text."""
    if not isinstance(s, str) or len(s) < 2:
        return False
    latin = sum(1 for c in s if ord(c) < 128 and c.isalpha())
    cjk = sum(1 for c in s if ord(c) >= 0x4E00)
    return latin > len(s)*0.5 and cjk == 0

def audit_entity_bundle(bundle_path: Path, output_dir: Path):
    """Scan entity bundle for untranslated English strings."""
    output_dir.mkdir(exist_ok=True)
    
    # Load translation coverage
    translated = set()
    for ln in Path('translation/state.jsonl').read_text('utf-8').splitlines():
        if ln.strip():
            r = json.loads(ln)
            tgt = r.get('manual') or r.get('machine')
            if tgt:
                translated.add(tgt)
    
    # Extract entity data
    with open(bundle_path, 'rb') as f:
        env = UnityPy.load(f)
    
    untranslated_strings = []
    string_stats = defaultdict(int)
    
    for obj in env.objects:
        if obj.type.name == 'TextAsset':
            try:
                data = json.loads(obj.read().script)
                if not isinstance(data, dict):
                    continue
                
                # Recursively extract all English-like strings
                def collect_strings(node, path=""):
                    if isinstance(node, dict):
                        for k, v in node.items():
                            collect_strings(v, f"{path}.{k}")
                    elif isinstance(node, list):
                        for i, item in enumerate(node):
                            collect_strings(item, f"{path}[{i}]")
                    elif isinstance(node, str) and is_english_like(node):
                        if node not in translated:
                            untranslated_strings.append({
                                'text': node,
                                'length': len(node),
                                'path': path
                            })
                        string_stats[path.split('.')[-1]] += 1
                
                collect_strings(data)
            except:
                pass
    
    # Write results
    untranslated_strings = list({s['text']: s for s in untranslated_strings}.values())
    untranslated_strings.sort(key=lambda x: -x['length'])
    
    # TSV output
    tsv_output = "text\tlength\tpath\n"
    for item in untranslated_strings:
        tsv_output += f"{item['text']}\t{item['length']}\t{item['path']}\n"
    
    (output_dir / "entity-untranslated.tsv").write_text(tsv_output)
    
    # Text output (one per line)
    (output_dir / "entity-untranslated.txt").write_text(
        '\n'.join(s['text'] for s in untranslated_strings)
    )
    
    # Summary
    print(f"Total untranslated: {len(untranslated_strings)}")
    print(f"Top fields: {dict(sorted(string_stats.items(), key=lambda x: -x[1])[:10])}")
    print(f"Wrote to {output_dir}")

if __name__ == "__main__":
    bundle = Path("backup/20260530-full-original/defaultlocalgroup_assets_assets_database_entitytextassets.asset_7658ed792f0c4924d06b11829a6c36d1.bundle")
    audit_entity_bundle(bundle, Path("docs"))
