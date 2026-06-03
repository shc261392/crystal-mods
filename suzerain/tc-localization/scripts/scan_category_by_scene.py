# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "UnityPy>=1.20",
#   "rich>=13.7",
# ]
# ///
"""Category-based comprehensive scan of scene bundles for untranslated content."""

import json
from pathlib import Path
from collections import defaultdict
import UnityPy
from rich.console import Console
from rich.table import Table

def is_english_like(s):
    if not isinstance(s, str) or len(s) < 2:
        return False
    latin = sum(1 for c in s if ord(c) < 128 and c.isalpha())
    cjk = sum(1 for c in s if ord(c) >= 0x4E00)
    return latin > len(s)*0.5 and cjk == 0

def extract_scene_strings(bundle_path: Path, scene_name: str):
    """Extract all English-like strings from a scene bundle."""
    strings_by_category = defaultdict(set)
    all_strings = {}
    
    with open(bundle_path, 'rb') as f:
        env = UnityPy.load(f)
    
    for obj in env.objects:
        if obj.type.name == 'MonoBehaviour':
            try:
                read_obj = obj.read()
                # Check for TextMeshProUGUI components
                if hasattr(read_obj, 'm_text'):
                    text = read_obj.m_text
                    if text and is_english_like(text):
                        all_strings[text] = ('TMP', obj.name)
                        # Categorize by component
                        if hasattr(read_obj, 'name'):
                            category = read_obj.name.split('/')[-1][:30]
                            strings_by_category[category].add(text)
            except:
                pass
    
    return dict(strings_by_category), all_strings

# Main scan
console = Console()
console.print("[bold cyan]Scene Bundle Category Scan[/]")

bundle_map = {
    "Sordland": Path("backup/20260530-full-original/scenes_scenes_assets_scenes_sordland.unity_6a29f2cab2ef8b301931a992da045ec1.bundle"),
    "Rizia": Path("backup/20260530-full-original/scenes_scenes_assets_scenes_rizia.unity_f3aa16cfb48dca20773754a9c19d5c1d.bundle"),
    "MainMenu": Path("backup/20260530-full-original/scenes_scenes_assets_scenes_mainmenu.unity_6dd6ca6b71e2733b13cf2860d4a95134.bundle"),
}

all_by_scene = {}
for scene_name, bundle_path in bundle_map.items():
    console.print(f"\n[yellow]Scanning {scene_name}...[/]")
    categories, strings = extract_scene_strings(bundle_path, scene_name)
    all_by_scene[scene_name] = {'categories': categories, 'all': strings}
    
    if categories:
        console.print(f"  Found {len(categories)} categories, {sum(len(v) for v in categories.values())} unique strings")
    else:
        console.print(f"  No untranslated English found (or already deployed)")

# Summary table
table = Table(title="Untranslated Content by Scene/Category")
table.add_column("Scene", style="cyan")
table.add_column("Categories", style="magenta")
table.add_column("Unique Strings", style="green")

for scene, data in all_by_scene.items():
    cat_count = len(data['categories'])
    str_count = sum(len(v) for v in data['categories'].values())
    table.add_row(scene, str(cat_count), str(str_count))

console.print(table)

# Output files
Path('docs').mkdir(exist_ok=True)
for scene, data in all_by_scene.items():
    if data['all']:
        # TSV output
        tsv = "text\tcategory\tcomponent_type\n"
        for text, (comp_type, comp_name) in data['all'].items():
            tsv += f"{text}\t{comp_name[:50]}\t{comp_type}\n"
        Path(f'docs/scan-{scene.lower()}-untranslated.tsv').write_text(tsv)

console.print(f"\n[green]✓ Scan complete. Output files written to docs/scan-*.tsv[/]")
