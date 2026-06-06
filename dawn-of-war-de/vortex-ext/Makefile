# Makefile — Vortex extension packaging
#
# The game extension is a CommonJS module that Vortex loads at startup.
# It must be packaged as a ZIP containing:
#   - info.json (manifest)
#   - index.js (extension code)
#   - gameart.jpg (640×360 game logo)

GAME_ID := warhammer40kdawnofwar
EXT_FOLDER := game-$(GAME_ID)
VERSION ?= $(shell jq -r '.version' $(EXT_FOLDER)/info.json)
PKG_NAME := vortex-$(GAME_ID)-v$(VERSION)
DIST_DIR := dist

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-z._-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  %-20s %s\n", $$1, $$2}'

.PHONY: clean
clean: ## Remove dist/ folder
	rm -rf "$(DIST_DIR)"

.PHONY: package
package: clean ## Build distributable Vortex extension ZIP
	@mkdir -p "$(DIST_DIR)"
	@echo "Packaging $(PKG_NAME).zip ..."
	@cd "$(EXT_FOLDER)" && \
	  zip -r "../$(DIST_DIR)/$(PKG_NAME).zip" . \
	    -x "*.DS_Store" \
	    -x "*.md" \
	    -x ".git*"
	@ls -lh "$(DIST_DIR)/$(PKG_NAME).zip"
	@echo "✓ $(DIST_DIR)/$(PKG_NAME).zip"
