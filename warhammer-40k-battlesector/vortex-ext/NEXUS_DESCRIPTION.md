# Nexus Mods Description — Battlesector Vortex Extension

## Short Description (max 250 chars)
Vortex Mod Manager extension for Warhammer 40,000: Battlesector. Required for installing mods through Vortex. Handles game detection, file deployment, and automatic backups.

---

## Full Description

Vortex Mod Manager Game Extension for Warhammer 40,000: Battlesector

This extension adds Warhammer 40,000: Battlesector support to Vortex Mod Manager, allowing you to easily install and manage mods for the game.

What This Extension Does:
- Automatically detects your Battlesector installation (Steam or GOG)
- Enables drag-and-drop mod installation in Vortex
- Handles deployment to the correct game directories
- Creates automatic backups of game files before modding (sharedassets1.assets)
- Provides one-click purge to restore original game files

How to Install:
1. Download this extension zip file
2. Open Vortex Mod Manager
3. Go to the Extensions tab
4. Drag and drop the zip file onto the Extensions panel
5. Click "Enable" when prompted

After installation, Battlesector will appear in Vortex's game list. You can then install mods by dragging mod zip files onto Vortex.

Technical Details:
- Supports Steam and GOG versions
- Auto-detects game installation via Steam App ID 1295500 and GOG App ID 1248481392
- Handles generic file replacement mods (sharedassets, bundles, catalog files)
- Smart wrapper folder detection and stripping for user convenience
- Creates one-time backup of sharedassets1.assets for safe reverting

This extension is required for using Battlesector mods with Vortex. It does not modify your game on its own.

Compatibility:
- Vortex v1.6.0 or later
- Warhammer 40,000: Battlesector (all versions)
