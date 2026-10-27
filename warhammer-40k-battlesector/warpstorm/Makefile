# Warpstorm — build Makefile
#
#   make build        THE release build (AGENTS.md rule 15): plugin + configurator
#                     -> dist/warpstorm-v<version>.zip, byte-identical for the same
#                     commit + game interop. No arguments during a release.
#   make plugin       dev: just the plugin DLL
#   make configurator dev: just the configurator (debug-style build, no zip)
#   make selftest     headless verify of the configurator pipeline
#   make package      alias of build
#   make clean
#
# Requires the .NET SDK (10.x here) and the game's BepInEx/interop assemblies
# (present after the BepInEx Framework mod has run once).
#
# GAME_DIR can be overridden, e.g.
#   make plugin GAME_DIR="/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector"

GAME_DIR ?= /mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector
PLUGIN   := plugin/Warpstorm.csproj
CONFIG   := configurator/Warpstorm.Configurator.csproj

.PHONY: build plugin configurator selftest package clean

build:
	bash package.sh

plugin:
	dotnet build $(PLUGIN) -c Release -p:GameDir="$(GAME_DIR)"

configurator:
	dotnet build $(CONFIG) -c Release

selftest:
	dotnet run --project $(CONFIG) -c Release -- --selftest

package: build

clean:
	rm -rf plugin/bin plugin/obj configurator/bin configurator/obj
	rm -rf .copilot_workspace/stage
	rm -f dist/warpstorm-*.zip
