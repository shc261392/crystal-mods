# ─────────────────────────────────────────────────────────────────────────────
# WH40K DoW:DE – Traditional Chinese Locale Mod
# Makefile — development env management and run command control
#
# Prerequisites (dev, Linux only):
#   - uv  (https://docs.astral.sh/uv/)
#   - bash, rsync
#
# IMPORTANT: run all targets from the repository root.
# ─────────────────────────────────────────────────────────────────────────────

SHELL := /bin/bash
.DEFAULT_GOAL := help

PYTHON   := uv run python
FONT_DIR := data/font
SCRIPTS  := scripts

# ── Font / size defaults (override on CLI: make apply FONT=noto-serif-tc SIZE=36)
FONT     ?= noto-sans-tc
SIZE     ?= 34
PROFILE  ?=
MODE     ?= fallback-only

# ─────────────────────────────────────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: setup
setup: ## Install Python environment (no relic SGA tools needed for most workflows)
	uv sync
	@echo ""
	@echo "✓ Python env ready.  Run 'make help' to see available commands."

.PHONY: setup-sga
setup-sga: ## Install relic SGA tools (required only for SGA repack; Windows/Wine only)
	uv sync --extra sga
	@echo "✓ relic-tool-sga installed.  Use 'make unpack-sga' to extract the archive."

# ─────────────────────────────────────────────────────────────────────────────
# Font patching
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: dry-run
dry-run: ## Preview font-fix changes without writing (SIZE / MODE overridable)
	$(PYTHON) $(SCRIPTS)/apply_font_fix.py \
	    --root . \
	    --restore-from-bak \
	    --mode $(MODE) \
	    --size $(SIZE) \
	    --dry-run

.PHONY: apply
apply: ## Apply font-fix to data/font/*.fnt (writes files; auto-creates .bak)
	$(PYTHON) $(SCRIPTS)/apply_font_fix.py \
	    --root . \
	    --restore-from-bak \
	    --mode $(MODE) \
	    --size $(SIZE)
	@echo ""
	@echo "✓ Font fix applied.  Run 'make deploy' to push to the game installation."

.PHONY: apply-tc
apply-tc: ## Apply Traditional Chinese text corrections to Engine.ucs
	$(PYTHON) $(SCRIPTS)/apply_tc_corrections.py --ucs Engine.ucs

.PHONY: dry-run-tc
dry-run-tc: ## Preview TC text corrections without writing
	$(PYTHON) $(SCRIPTS)/apply_tc_corrections.py --ucs Engine.ucs --dry-run

.PHONY: list-fonts
list-fonts: ## List font replacement options (--replace-font-file / --replace-font-match)
	@echo "Font replacement options:"
	@echo "  --replace-font-file FILE   e.g. msyh.ttc, notosans_m_16_xc"
	@echo "  --replace-font-match REGEX e.g. NotoSansTC|Gulim (default)"

.PHONY: list-profiles
list-profiles: ## Show size/mode options
	@echo "Size: set via SIZE=N (default: 34)  Mode: fallback-only | all (default: fallback-only)"

# ─────────────────────────────────────────────────────────────────────────────
# SGA archive tools (optional, Windows/Wine)
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: unpack-sga
unpack-sga: ## Unpack EnginLoc.sga → data/ (requires setup-sga; Windows/Wine only)
	@echo "Unpack is Windows-only (PowerShell + relic.exe)."
	@echo "On Linux use: uv run python scripts/apply_font_fix.py directly (no SGA needed)."

# ─────────────────────────────────────────────────────────────────────────────
# Deployment
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: deploy
deploy: ## Deploy mod (loose-file mode, default) — copies data/, disables EnginLoc.sga
	@bash deploy.sh

.PHONY: deploy-sga
deploy-sga: ## Deploy mod (sga mode) — builds EnginLocMod.sga, keeps EnginLoc.sga active
	@bash deploy.sh --mode sga

.PHONY: deploy-dry
deploy-dry: ## Dry-run the default (loose) deploy without writing anything
	@bash deploy.sh --dry-run

.PHONY: deploy-sga-dry
deploy-sga-dry: ## Dry-run the sga deploy without writing anything
	@bash deploy.sh --mode sga --dry-run

.PHONY: uninstall
uninstall: ## Revert deployment (restore backups, re-enable original SGA)
	@bash uninstall.sh

DIST_DIR  := dist
VERSION   := $(shell python3 -c "import json,pathlib; print(json.loads(pathlib.Path('modinfo.json').read_text())['version'])" 2>/dev/null || echo "dev")
PKG_NAME  := wh40k-dow-de-tc-mod-v$(VERSION)
EXT_DIR   := vortex-ext/game-warhammer40kdawnofwar
EXT_ID    := game-warhammer40kdawnofwar
EXT_VER   := $(shell python3 -c "import json,pathlib; print(json.loads(pathlib.Path('$(EXT_DIR)/info.json').read_text())['version'])" 2>/dev/null || echo "dev")
EXT_NAME  := vortex-ext-$(EXT_ID)-v$(EXT_VER)

# ─────────────────────────────────────────────────────────────────────────────
# Packaging
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: package
package: ## Build distributable mod archive (flat zip: EnginLocMod.sga + Engine.ucs + metadata at root)
	@echo "▶ Packaging $(PKG_NAME).zip ..."
	@rm -rf "$(DIST_DIR)/$(PKG_NAME)" "$(DIST_DIR)/$(PKG_NAME).zip"
	@mkdir -p "$(DIST_DIR)/$(PKG_NAME)"
	@cp EnginLocMod.sga "$(DIST_DIR)/$(PKG_NAME)/"
	@cp Engine.ucs "$(DIST_DIR)/$(PKG_NAME)/"
	@cp modinfo.json README.md FONT_FIX_README.md "$(DIST_DIR)/$(PKG_NAME)/"
	@cp deploy.sh deploy.ps1 uninstall.sh uninstall.ps1 "$(DIST_DIR)/$(PKG_NAME)/"
	@cp Makefile "$(DIST_DIR)/$(PKG_NAME)/"
	@rsync -a docs/ "$(DIST_DIR)/$(PKG_NAME)/docs/"
	@rsync -a scripts/ "$(DIST_DIR)/$(PKG_NAME)/scripts/"
	@cd "$(DIST_DIR)/$(PKG_NAME)" && zip -r "../$(PKG_NAME).zip" . -x "*.DS_Store"
	@echo "✓ $(DIST_DIR)/$(PKG_NAME).zip"
	@echo "  Size: $$(du -sh "$(DIST_DIR)/$(PKG_NAME).zip" | cut -f1)"
	@echo "  Files: $$(find "$(DIST_DIR)/$(PKG_NAME)" -type f | wc -l)"

.PHONY: package-ext
package-ext: ## Build Vortex extension zip (.copilot_workspace/dist/vortex-ext-*.zip)
	@echo "▶ Packaging Vortex extension $(EXT_NAME).zip ..."
	@rm -rf "$(DIST_DIR)/$(EXT_NAME)"
	@rm -f "$(DIST_DIR)/$(EXT_NAME).zip"
	@mkdir -p "$(DIST_DIR)/$(EXT_NAME)"
	@cp "$(EXT_DIR)/index.js"  "$(DIST_DIR)/$(EXT_NAME)/"
	@cp "$(EXT_DIR)/info.json" "$(DIST_DIR)/$(EXT_NAME)/"
	@[ -f "$(EXT_DIR)/gameart.jpg" ] && cp "$(EXT_DIR)/gameart.jpg" "$(DIST_DIR)/$(EXT_NAME)/" || true
	@cd "$(DIST_DIR)/$(EXT_NAME)" && zip -r "../$(EXT_NAME).zip" . -x "*.DS_Store"
	@rm -rf "$(DIST_DIR)/$(EXT_NAME)"
	@echo "✓ $(DIST_DIR)/$(EXT_NAME).zip"
	@echo "  Size: $$(du -sh "$(DIST_DIR)/$(EXT_NAME).zip" | cut -f1)"
	@echo "  Files: $$(unzip -l "$(DIST_DIR)/$(EXT_NAME).zip" | tail -1)"

.PHONY: package-all
package-all: package package-ext package-keybinds ## Build both the mod archive and Vortex extension zip

# ─────────────────────────────────────────────────────────────────────────────
# Keybinding Overhaul mod (separate, ships standalone)
# ─────────────────────────────────────────────────────────────────────────────

KEYBINDS_VER     ?= 1.0.0
KEYBINDS_SRC_DIR := mod/keybinds
KEYBINDS_PRESETS := vanilla wasd-camera wasd-camera-ingame

.PHONY: keybinds-build
keybinds-build: ## Regenerate keybind presets from mod/keybinds/stock/keydefaults.lua
	$(PYTHON) $(SCRIPTS)/build_keybind_presets.py --clean

.PHONY: package-keybinds
package-keybinds: keybinds-build ## Build one zip per keybind preset under $(DIST_DIR)/
	@for preset in $(KEYBINDS_PRESETS); do \
	    pkg="wh40k-dow-de-keybinds-$$preset-v$(KEYBINDS_VER)"; \
	    echo "▶ Packaging $$pkg.zip ..."; \
	    rm -rf "$(DIST_DIR)/$$pkg" "$(DIST_DIR)/$$pkg.zip"; \
	    mkdir -p "$(DIST_DIR)/$$pkg"; \
	    rsync -a --exclude='HOTKEYS.md' "$(KEYBINDS_SRC_DIR)/presets/$$preset/" "$(DIST_DIR)/$$pkg/"; \
	    cp "$(KEYBINDS_SRC_DIR)/presets/$$preset/HOTKEYS.md" "$(DIST_DIR)/$$pkg/HOTKEYS.md"; \
	    cp "$(KEYBINDS_SRC_DIR)/README.md" "$(DIST_DIR)/$$pkg/README.md"; \
	    (cd "$(DIST_DIR)/$$pkg" && zip -rq "../$$pkg.zip" . -x "*.DS_Store"); \
	    echo "✓ $(DIST_DIR)/$$pkg.zip"; \
	    echo "  Size: $$(du -sh "$(DIST_DIR)/$$pkg.zip" | cut -f1)"; \
	done

# ─────────────────────────────────────────────────────────────────────────────
# Maintenance
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: restore-bak
restore-bak: ## Restore all .fnt files from their .bak backups (undo apply)
	$(PYTHON) $(SCRIPTS)/apply_font_fix.py --root . --dry-run --restore-from-bak --size 34 2>/dev/null || true
	@find $(FONT_DIR) -name "*.fnt.bak" -exec sh -c 'cp "$$1" "$${1%.bak}"' _ {} \;
	@echo "✓ .fnt files restored from .bak"

.PHONY: clean
clean: ## Remove uv cache and .venv (does NOT touch mod data or backups)
	rm -rf .venv
	uv cache clean 2>/dev/null || true
	@echo "✓ Clean done."

# ─────────────────────────────────────────────────────────────────────────────
# Help
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: help
help: ## Show this help message
	@printf "\033[1mWH40K DoW:DE TC Mod — available targets\033[0m\n\n"
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) \
	    | sort \
	    | awk 'BEGIN{FS=":.*## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@printf "\nOverridable variables: FONT (default: $(FONT)), SIZE (default: $(SIZE)), MODE (default: $(MODE)), PROFILE\n"
	@printf "Example: make apply FONT=noto-serif-tc SIZE=36\n"
