# ─────────────────────────────────────────────────────────────────────────────
# Suzerain – Traditional Chinese (zh-TW) Localisation
# Makefile — extraction, translation, repack, packaging
#
# Prerequisites (dev, Linux/WSL2):
#   - uv  (https://docs.astral.sh/uv/)
#   - GEMINI_API_KEY in repo-root .env  (for translation only)
#
# Run all targets from THIS directory (suzerain/tc-localization/).
# ─────────────────────────────────────────────────────────────────────────────

SHELL := /bin/bash
.DEFAULT_GOAL := help

# ── Paths ────────────────────────────────────────────────────────────────────
REPO_ROOT   := $(abspath ../..)
SCRIPTS     := scripts
PROJECT     := translation
EXTRACTED   := extracted
BUILD       := build

# Original game bundle (override GAME_DIR to point at your install).
GAME_DIR    ?= /mnt/d/SteamLibrary/steamapps/common/Suzerain
AA_REL      := Suzerain_Data/StreamingAssets/aa/StandaloneWindows64
BUNDLE_NAME := defaultlocalgroup_assets_assets_database_entitytextassets.asset_7658ed792f0c4924d06b11829a6c36d1.bundle
SRC_BUNDLE  := $(GAME_DIR)/$(AA_REL)/$(BUNDLE_NAME)
OUT_BUNDLE  := $(BUILD)/$(BUNDLE_NAME)

# ── Help ─────────────────────────────────────────────────────────────────────
.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ── Extraction ───────────────────────────────────────────────────────────────
.PHONY: extract
extract: ## Extract strings from the game bundle into extracted/ (re-run if game updated)
	uv run --script $(SCRIPTS)/extract_entitytext.py "$(SRC_BUNDLE)" --out $(EXTRACTED)
	uv run --script $(SCRIPTS)/build_tl_source.py $(EXTRACTED)/raw_strings.jsonl \
	    --out $(PROJECT)/source.jsonl

# ── Glossary ─────────────────────────────────────────────────────────────────
.PHONY: glossary
glossary: ## Build the corpus-driven glossary (requires GEMINI_API_KEY)
	set -a && . $(REPO_ROOT)/.env && set +a && \
	  uv run tl glossary build $(PROJECT) --min-count 8 --max-terms 400 \
	    --context "Suzerain, a political-strategy narrative game set in the fictional republic of Sordland"

# ── Translation ──────────────────────────────────────────────────────────────
.PHONY: translate
translate: ## Run the full Gemini translation pass (requires GEMINI_API_KEY)
	set -a && . $(REPO_ROOT)/.env && set +a && \
	  uv run tl translate $(PROJECT) --backend gemini --batch-size 25

.PHONY: status
status: ## Show translation status counts
	uv run tl status $(PROJECT)

# ── Repack / build ───────────────────────────────────────────────────────────
.PHONY: build
build: ## Repack the translated bundle into build/ (uses final else machine text)
	@mkdir -p $(BUILD)
	uv run --script $(SCRIPTS)/repack_entitytext.py "$(SRC_BUNDLE)" \
	    --project $(PROJECT) --out "$(OUT_BUNDLE)"
	@echo "✓ Patched bundle → $(OUT_BUNDLE)"

.PHONY: clean
clean: ## Remove the build/ output
	rm -rf $(BUILD)

# ── Deploy (thin wrappers; prefer the scripts directly for full options) ──────
.PHONY: deploy
deploy: build ## Build then install into the game (Linux/WSL2)
	bash deploy.sh --game-dir "$(GAME_DIR)"

.PHONY: uninstall
uninstall: ## Restore the original bundle from the latest backup
	bash uninstall.sh --game-dir "$(GAME_DIR)"
