# Data-edit reference implementation

`build.py` is the worked example behind
[`../../data_edit_tutorial.md`](../../data_edit_tutorial.md), preserved from the
retired **Superhuman Cadian** demo mod.

It demonstrates the complete UnityPy data-edit path:

1. load a pristine `startup_assets_all.bundle`;
2. locate `UnitDataTable` / `WeaponDataTable` by `m_Name`;
3. edit only the safe numeric fields (explicit allow-list);
4. save with the original packer;
5. stage the game-root-relative path and write a byte-deterministic zip;
6. re-open the result and assert the patched values.

## Usage

```bash
uv run --no-project --with UnityPy python build.py        # build -> dist/
uv run --no-project --with UnityPy python build.py dump   # inspect base values
```

Build inputs (env-overridable):

- `BS_GAME_DIR` — game install folder
- `BS_VANILLA_BUNDLE` — pristine `startup_assets_all.bundle`
  (default: the game folder's `.vortex_backup`)

Output: `dist/superhuman-cadian-v1.0.1.zip`, containing only
`Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle`.

Copy the script and replace the config block (`UNIT_ID`, `UNIT_SCALE_FIELDS`,
`UNIT_ABSOLUTE_FIELDS`, `WEAPON_PATCHES`) to target another unit or weapon.

> Single-player only. This replaces a core game file and conflicts with any other
> mod that modifies `startup_assets_all.bundle`.
