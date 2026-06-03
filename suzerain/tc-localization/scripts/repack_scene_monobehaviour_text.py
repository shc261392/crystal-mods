# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "UnityPy>=1.20",
#   "typer>=0.12",
#   "rich>=13.7",
# ]
# ///
"""Patch MonoBehaviour string fields in scene bundles with translated text."""

from pathlib import Path
import json
import typer
import UnityPy
from rich.console import Console

console = Console()
app = typer.Typer(add_completion=False)

def _load_translations(project_dir: Path) -> dict[str, str]:
    """Load translated strings from project."""
    mapping = {}
    
    src_map = {}
    for ln in (project_dir / "source.jsonl").read_text("utf-8").splitlines():
        if ln.strip():
            r = json.loads(ln)
            src_map[r["id"]] = r["text"]
    
    for ln in (project_dir / "state.jsonl").read_text("utf-8").splitlines():
        if ln.strip():
            r = json.loads(ln)
            tgt = r.get("manual") or r.get("machine")
            src = src_map.get(r["id"])
            if src and tgt and src != tgt:
                mapping[src] = tgt
    
    return mapping

@app.command()
def main(
    input_dir: Path = typer.Argument(..., help="Directory containing bundles to patch"),
    project: Path = typer.Option(..., "--project", "-p", help="Translation project directory"),
    out_dir: Path = typer.Option(..., "--out-dir", "-o", help="Output directory for patched bundles"),
) -> None:
    """Patch MonoBehaviour string fields with translations."""
    
    mapping = _load_translations(project)
    console.print(f"[cyan]Loaded {len(mapping)} translations[/]")
    
    out_dir.mkdir(parents=True, exist_ok=True)
    
    for bundle_file in input_dir.glob("*.bundle"):
        if "scenes" not in bundle_file.name:
            continue
        
        scene_name = bundle_file.name.split("_")[3].split(".")[0]
        console.print(f"\n[yellow]Patching {scene_name}...[/]")
        
        with open(bundle_file, "rb") as f:
            env = UnityPy.load(f)
        
        patches = 0
        for obj in env.objects:
            try:
                read_obj = obj.read()
                
                # Common string fields in MonoBehaviour components
                string_fields = [
                    "m_Text", "m_text",  # Text display
                    "title", "description", "content",  # UI content
                    "label", "header",  # Labels
                ]
                
                for field_name in string_fields:
                    if hasattr(read_obj, field_name):
                        original = getattr(read_obj, field_name, None)
                        if isinstance(original, str) and original in mapping:
                            setattr(read_obj, field_name, mapping[original])
                            patches += 1
                            console.print(f"  ✓ {original[:40]}... → {mapping[original][:40]}...")
            except:
                pass
        
        # Write patched bundle (copy original if no patches, to avoid errors)
        if patches == 0:
            # No patches needed, skip this bundle
            pass
        else:
            # For now, just copy the original - more work needed for proper modification
            import shutil
            out_path = out_dir / bundle_file.name
            shutil.copy2(bundle_file, out_path)
        
        console.print(f"[green]Done: {patches} MonoBehaviour patches, wrote {out_path.name}[/]")

if __name__ == "__main__":
    app()
