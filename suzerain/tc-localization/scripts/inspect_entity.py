# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "UnityPy>=1.20",
# ]
# ///
import json
from pathlib import Path
import UnityPy

bundle_path = Path("backup/20260530-full-original/defaultlocalgroup_assets_assets_database_entitytextassets.asset_7658ed792f0c4924d06b11829a6c36d1.bundle")
with open(bundle_path, 'rb') as f:
    env = UnityPy.load(f)

for obj in env.objects:
    if obj.type.name == 'TextAsset':
        data = obj.read().m_Script
        parsed = json.loads(data)
        items = parsed.get('items', [])
        print(f"Items count: {len(items)}")
        if items:
            print(f"\nFirst item keys: {list(items[0].keys())[:15] if isinstance(items[0], dict) else type(items[0])}")
            # Look for character data
            for i, item in enumerate(items[:2]):
                print(f"\n--- Item {i} ---")
                if isinstance(item, dict):
                    for k in list(item.keys())[:8]:
                        v = item[k]
                        if isinstance(v, str) and len(v) < 100:
                            print(f"  {k}: {v}")
                        elif isinstance(v, (int, float, bool)):
                            print(f"  {k}: {v}")
                        else:
                            print(f"  {k}: {type(v).__name__}")
        break
