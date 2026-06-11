# Black Book Vortex Extension

This extension adds full localization support for **Black Book** (Steam App ID 1138660) via Vortex.

## Features

- **Auto-discovery**: Finds Black Book via Steam App ID
- **Localization installer**: Routes localization asset mods to `Black Book_Data/resources/` and `StreamingAssets/`
- **Font handler**: Deploys font assets (`.ttf`, `.otf`, `.asset`) to `Black Book_Data/Resources/Fonts/`
- **Wrapper stripping**: Automatically removes single wrapper folders for user convenience
- **Multi-platform**: Supports Windows native, WSL2, and Linux/Proton

## Supported Mod Types

1. **Localization mods** — Unity `.asset` files containing TC strings (zh-TW/zh_TW naming)
2. **Font mods** — `.ttf`, `.otf`, `.asset` files or folders in `Fonts/` 
3. **General mods** — any files with game-root-relative paths

## Installation

1. Download `vortex-ext-game-black-book-v*.zip` from Nexus Mods
2. Drag and drop it onto Vortex's **Extensions** tab
3. Click **Enable**
4. Re-open Vortex — **Black Book** will appear under *Supported Games*

## Using with Localization Mods

Once installed, you can use this extension to deploy TC (Traditional Chinese) or any other localization mods.

### Example: TC Localization Mod

1. Download the TC localization mod zip
2. Drag it onto Vortex's **Mods** tab
3. Click **Deploy Mods**
4. Launch the game — text should appear in Traditional Chinese

## Uninstall

Click *Purge Mods* in Vortex to remove all deployed mods and restore the game to its original state.

