# ─────────────────────────────────────────────────────────────────────────────
# WH40K Battlesector – Traditional Chinese Localization Mod
# Makefile — build and deployment tasks
#
# Prerequisites:
#   - Python 3.8+ with UnityPy (pip install UnityPy)
#   - bash
#
# IMPORTANT: run all targets from the repository root (tc-localization folder).
# ─────────────────────────────────────────────────────────────────────────────

SHELL := /bin/bash
.DEFAULT_GOAL := help

PYTHON   := python3
SCRIPTS  := tools/scripts

# ─────────────────────────────────────────────────────────────────────────────
# Help
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: help
help: ## Show this help message
	@grep -E '^\S+:.*?## ' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# ─────────────────────────────────────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: setup
setup: ## Install Python dependencies (UnityPy required)
	pip install -r requirements.txt 2>/dev/null || pip install UnityPy
	@echo "✓ Python environment ready."

# ─────────────────────────────────────────────────────────────────────────────
# Build
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: build
build: ## Build patched asset file (full pipeline)
	$(PYTHON) $(SCRIPTS)/extract_loc.py
	$(PYTHON) $(SCRIPTS)/build_patch.py
	$(PYTHON) $(SCRIPTS)/patch_font.py
	$(PYTHON) $(SCRIPTS)/inject_loc.py
	@echo "✓ Build complete. Output: dist/"

.PHONY: extract
extract: ## Extract game asset strings (source/)
	$(PYTHON) $(SCRIPTS)/extract_loc.py

.PHONY: patch-font
patch-font: ## Apply font patches to glyph assets
	$(PYTHON) $(SCRIPTS)/patch_font.py

.PHONY: inject
inject: ## Inject TC strings into game assets (dist/)
	$(PYTHON) $(SCRIPTS)/inject_loc.py

.PHONY: analyze
analyze: ## Analyze translation coverage and missing glyphs
	$(PYTHON) $(SCRIPTS)/analyze.py

# ─────────────────────────────────────────────────────────────────────────────
# Deploy
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: deploy
deploy: ## Deploy to game (auto-detect via Steam)
	bash deploy.sh

.PHONY: deploy-dry
deploy-dry: ## Preview deployment without writing files
	bash deploy.sh --dry-run

.PHONY: deploy-manual
deploy-manual: ## Deploy to specific game directory
	@read -p "Game directory: " GAME_DIR; bash deploy.sh --game-dir "$$GAME_DIR"

.PHONY: uninstall
uninstall: ## Uninstall mod and restore original assets
	bash uninstall.sh

# ─────────────────────────────────────────────────────────────────────────────
# Development
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: lint
lint: ## Check source translation files for syntax errors
	$(PYTHON) $(SCRIPTS)/lint.py

.PHONY: extract-glyphs
extract-glyphs: ## Extract missing glyphs from latest Player.log
	$(PYTHON) $(SCRIPTS)/extract_missing_glyphs.py --tail-lines 20000

.PHONY: clean
clean: ## Remove extracted/patched intermediate files
	rm -rf source/ patched/ dist/

.PHONY: clean-all
clean-all: clean ## Remove all generated files including backups
	rm -rf backup/

.PHONY: .PHONY
.PHONY:
	@echo "Phony targets defined."
