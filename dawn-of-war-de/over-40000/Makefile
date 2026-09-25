# ─────────────────────────────────────────────────────────────────────────────
# "Over 40000" — DoW DE power-cheat mod
# Makefile — auto-extract game data, regenerate mod, build Vortex zip
#
# Prerequisites (dev, Linux/WSL2):
#   - python3 (stdlib only for generator; pip for the SGA extractor)
#   - zip
#
# The generated binary data (mod/) is NOT tracked in git — it is rebuilt from
# the Dawn of War Definitive Edition installation. The game directory is
# auto-detected from Steam library folders, or set via DOW_GAME_DIR / --game-dir.
#
# Run all targets from this directory.
# ─────────────────────────────────────────────────────────────────────────────

SHELL := /bin/bash
.DEFAULT_GOAL := help

PYTHON   := python3
MOD_DIR  := mod
DIST_DIR := dist
SCRIPTS  := scripts

# Version. The release is 0.1.7 (0.1.6 crash-fixed + module-scoped single-model
# exclusions + experimental Necron production-speed cheat). Vanilla single-model
# campaign variants are excluded in W40k/WXP and in DXP2/DXP3, where the
# base-game validator / mission-start min-loadout spawn would crash or freeze.
#
# The release set is TWO zips; `make build` with NO arguments builds BOTH:
#   over-40000-v0.1.7.zip                  (resource cheat on)
#   over-40000-v0.1.7-normal-resources.zip (no resource cheat)
# Ad-hoc per-variant invocations (RESOURCE_CHEAT=…, SQUAD_SCALE=…) are
# experimental/diagnostic ONLY and forbidden for formal releases (AGENTS.md
# hard rule 15).
VERSION      := 0.1.7
SQUAD_SCALE  ?= 5      ## multiply squad unit_min/unit_max by N (0 = off)
RESOURCE_CHEAT ?= 1    ## 1 = start with 40001 req/power + x10 income

ifeq ($(RESOURCE_CHEAT),0)
PKG_NAME := over-40000-v$(VERSION)-normal-resources
else
PKG_NAME := over-40000-v$(VERSION)
endif

# Where the SGA extraction tree lives (gitignored scratch space).
# Resolves to the workspace root's .copilot_workspace/extract
# (repo contract: mods live at <game>/<mod>/ = 2 levels deep).
EXTRACT_ROOT ?= ../../.copilot_workspace/extract
# Optional: override the auto-detected game dir. Also respects $DOW_GAME_DIR.
GAME_DIR ?=

# ─────────────────────────────────────────────────────────────────────────────
# Help
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: help
help:
	@echo "Over 40000 - DoW DE power-cheat mod"
	@echo ""
	@echo "Targets:"
	@echo "  make build        (re)generate mod/ from the game install and build the Vortex zip"
	@echo "  make regenerate   auto-extract game data (if needed) and regenerate mod/"
	@echo "  make lint         Ruff-lint the generator scripts"
	@echo "  make verify       Sanity-check the generated mod/ tree"
	@echo "  make clean        Remove build artifacts"
	@echo ""
	@echo "make build builds the full release set (both zips) with NO arguments."
	@echo "Infra path overrides (not content): make build EXTRACT_ROOT=... GAME_DIR=...  (or set DOW_GAME_DIR)"
	@echo "Experimental ONLY (never for a release): make build SQUAD_SCALE=N / RESOURCE_CHEAT=0|1"

# ─────────────────────────────────────────────────────────────────────────────
# Regenerate mod tree from the game install
# ─────────────────────────────────────────────────────────────────────────────

GAME_ARG := $(if $(GAME_DIR),--game-dir $(GAME_DIR))
# Weapon-cap boost is OFF by default (generate_mod.py default): the
# Over40000_BoostWeaponCaps block crashed the game (nil Squad_GetUpgradeMax * 4)
# and was removed from the recommended build. Pass --weapon-cap-boost on to
# force it in (diagnostics only).
GEN_ARGS := --squad-scale $(SQUAD_SCALE) --resource-cheat $(if $(filter 1,$(RESOURCE_CHEAT)),on,off) --exclude-single-model on --descale-campaign-single on

.PHONY: regenerate
regenerate: ## Auto-extract game data (if missing) and regenerate mod/
	$(PYTHON) $(SCRIPTS)/ensure_extract.py --extract-root "$(EXTRACT_ROOT)" $(GAME_ARG)
	$(PYTHON) $(SCRIPTS)/generate_mod.py "$(EXTRACT_ROOT)" "$(MOD_DIR)" $(GEN_ARGS)

# ─────────────────────────────────────────────────────────────────────────────
# Build Vortex zips
# ─────────────────────────────────────────────────────────────────────────────

# The release build: `make build` with NO arguments produces the complete
# release zip set (one zip per variant), deterministically, from the committed
# generator + blacklist. Each variant regenerates into a CLEAN mod/ so no
# variant leaks files into another. Ad-hoc content args are forbidden for
# formal releases (AGENTS.md hard rule 15).
.PHONY: build build-cheat build-normal
build: build-cheat build-normal ## Build ALL release zips: resource-cheat + normal-resources (no args)

build-cheat:   ## internal: (re)build the resource-cheat zip
	$(MAKE) _build-variant RESOURCE_CHEAT=1

build-normal:  ## internal: (re)build the normal-resources zip
	$(MAKE) _build-variant RESOURCE_CHEAT=0

.PHONY: _build-variant
_build-variant: ## internal: regenerate + verify + package one variant (RESOURCE_CHEAT comes from the caller)
	@rm -rf "$(MOD_DIR)"
	$(MAKE) regenerate verify package-zip

.PHONY: package
package: build ## Alias for 'build'

# Zip-only helper (used by build.sh / build.ps1 after they regenerate + verify).
# Packaging is deterministic (scripts/package_zip.py) so `make build` yields
# byte-identical zips for the same commit + game data (AGENTS.md hard rule 15).
.PHONY: package-zip
package-zip:
	@rm -rf "$(DIST_DIR)/$(PKG_NAME)" "$(DIST_DIR)/$(PKG_NAME).zip"
	@mkdir -p "$(DIST_DIR)/$(PKG_NAME)"
	@cp -r "$(MOD_DIR)"/W40k "$(MOD_DIR)"/WXP "$(MOD_DIR)"/DXP2 "$(MOD_DIR)"/DXP3 "$(DIST_DIR)/$(PKG_NAME)/"
	$(PYTHON) $(SCRIPTS)/package_zip.py "$(DIST_DIR)/$(PKG_NAME)" "$(DIST_DIR)/$(PKG_NAME).zip"
	@echo "  Size: $$(du -sh "$(DIST_DIR)/$(PKG_NAME).zip" | cut -f1)"
	@echo "  Files: $$(find "$(DIST_DIR)/$(PKG_NAME)" -type f | wc -l)"

# ─────────────────────────────────────────────────────────────────────────────
# Verification / lint
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: verify
verify: ## Sanity-check the generated mod tree
	@test -f "$(MOD_DIR)/W40k/Data/scar/setup.scar" || { echo "ERROR: setup.scar missing"; exit 1; }
	@n=$$(find "$(MOD_DIR)" -path '*racebps*' -name '*.rgd' | wc -l); echo "  patched race files: $$n"; \
	  [ "$$n" -ge 25 ] || { echo "ERROR: too few race patches"; exit 1; }
	@n=$$(find "$(MOD_DIR)" -path '*sbps*' -name '*.rgd' | wc -l); echo "  patched squad files: $$n"; \
	  [ "$$n" -gt 250 ] || { echo "ERROR: too few squad patches"; exit 1; }
	@n=$$(find "$(MOD_DIR)" -name '*.lua' | wc -l); \
	  [ "$$n" -eq 0 ] || { echo "ERROR: unexpected .lua data overrides present"; exit 1; }
	@echo "✓ mod/ tree looks valid"

.PHONY: lint
lint: ## Ruff-lint the generator scripts (needs uv / ruff)
	uvx ruff check scripts/ 2>/dev/null || ruff check scripts/ 2>/dev/null || echo "note: ruff not installed, skipping"

.PHONY: test
test: ## Run the generator invariant unit tests (needs the extraction tree)
	python3 scripts/test_cost_counter_scale.py

.PHONY: clean
clean: ## Remove build artifacts
	rm -rf "$(DIST_DIR)"

.PHONY: dist
dist: build ## Alias for 'build'
