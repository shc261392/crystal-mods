# ─────────────────────────────────────────────────────────────────────────────
# "Easy Reinforcement" - DoW DE standalone mod
# Makefile - build the Vortex-installable zip
#
# The mod ships an always-on wincondition in the W40k module
# (Data/scar/winconditions/easyreinforce.*). A single W40k copy is enough: the
# engine resolves always-on winconditions for every mission (base, Winter
# Assault, Dark Crusade, Soulstorm), and shipping extra copies in other modules
# would register duplicate 1s rules. No game-data patching is needed.
# ─────────────────────────────────────────────────────────────────────────────

SHELL := /bin/bash
.DEFAULT_GOAL := help

MOD_DIR  := mod
DIST_DIR := dist
VERSION  := 0.1.3
PKG_NAME := easy-reinforcement-v$(VERSION)

.PHONY: help
help:
	@echo "Easy Reinforcement - DoW DE standalone mod"
	@echo ""
	@echo "  make build     build the Vortex-installable zip in $(DIST_DIR)/"
	@echo "  make verify    sanity-check the mod tree"
	@echo "  make clean     remove build artifacts"

.PHONY: verify
verify: ## Sanity-check the mod tree
	@test -f "$(MOD_DIR)/W40k/Data/scar/winconditions/easyreinforce.scar" || \
	  { echo "ERROR: easyreinforce.scar missing"; exit 1; }
	@test -f "$(MOD_DIR)/W40k/Data/scar/winconditions/easyreinforce_local.lua" || \
	  { echo "ERROR: easyreinforce_local.lua missing"; exit 1; }
	@echo "✓ mod/ tree looks valid"

.PHONY: build
build: verify ## Package $(PKG_NAME).zip
	@rm -rf "$(DIST_DIR)/$(PKG_NAME)" "$(DIST_DIR)/$(PKG_NAME).zip"
	@mkdir -p "$(DIST_DIR)/$(PKG_NAME)"
	@cp -r "$(MOD_DIR)/W40k" "$(DIST_DIR)/$(PKG_NAME)/"
	@cd "$(DIST_DIR)/$(PKG_NAME)" && zip -r "../$(PKG_NAME).zip" . -x "*.DS_Store" >/dev/null
	@echo "✓ $(DIST_DIR)/$(PKG_NAME).zip"
	@echo "  Size: $$(du -sh "$(DIST_DIR)/$(PKG_NAME).zip" | cut -f1)"
	@echo "  Files: $$(find "$(DIST_DIR)/$(PKG_NAME)" -type f | wc -l)"

.PHONY: package
package: build ## Alias for 'build'

.PHONY: clean
clean: ## Remove build artifacts
	rm -rf "$(DIST_DIR)"