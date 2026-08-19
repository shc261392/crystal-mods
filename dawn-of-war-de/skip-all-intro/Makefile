# ─────────────────────────────────────────────────────────────────────────────
# skip-all-intro — DoW DE "skip all intro movies" mod
# Makefile — generate replacement movies, build Vortex zip
#
# Prerequisites (dev, Linux/WSL2): python3 and zip.
#
# The replacement movies (mod/) are NOT tracked in git — they are fully
# reproducible from scripts/generate_movies.py (0-byte stubs).
# dist/ is the build output (Vortex-installable zip).
#
# Run all targets from this directory.
# ─────────────────────────────────────────────────────────────────────────────

SHELL := /bin/bash
.DEFAULT_GOAL := help

PYTHON   := python3
VERSION  ?= 0.1.0
PKG_NAME := skip-all-intro-v$(VERSION)

# ─────────────────────────────────────────────────────────────────────────────
# Help
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: help
help:
	@echo "skip-all-intro - DoW DE skip-all-intro movies mod"
	@echo ""
	@echo "Targets:"
	@echo "  make build     generate mod/ replacement movies and build the Vortex zip"
	@echo "  make generate  only (re)generate the mod/ replacement movies"
	@echo "  make verify    sanity-check the generated mod/ tree"
	@echo "  make lint      Ruff-lint the generator script (optional)"
	@echo "  make clean     remove build artifacts"
	@echo ""
	@echo "Overrides: make build VERSION=0.1.1"

# ─────────────────────────────────────────────────────────────────────────────
# Generate replacement movies
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: generate
generate: ## (Re)generate the mod/ replacement movies
	@rm -rf mod
	$(PYTHON) scripts/generate_movies.py mod

# ─────────────────────────────────────────────────────────────────────────────
# Build Vortex zip
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: build
build: generate verify ## Generate + verify + package $(PKG_NAME).zip
	@rm -rf "dist/$(PKG_NAME)" "dist/$(PKG_NAME).zip"
	@mkdir -p "dist/$(PKG_NAME)"
	@cp -r mod/Engine mod/DXP2 mod/DXP3 "dist/$(PKG_NAME)/"
	@cd "dist/$(PKG_NAME)" && zip -r "../$(PKG_NAME).zip" . -x "*.DS_Store" >/dev/null
	@echo "✓ dist/$(PKG_NAME).zip"
	@echo "  Size: $$(du -sh "dist/$(PKG_NAME).zip" | cut -f1)"
	@echo "  Files: $$(find "dist/$(PKG_NAME)" -type f | wc -l)"

.PHONY: package
package: build ## Alias for 'build'

# ─────────────────────────────────────────────────────────────────────────────
# Verification / lint
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: verify
verify: ## Sanity-check the generated mod/ tree
	@n=$$(find mod -type f | wc -l); echo "  replacement movies: $$n"; \
	  [ "$$n" -eq 9 ] || { echo "ERROR: expected 9 replacement movies"; exit 1; }
	@test -f mod/Engine/Movies/blur_intro.webm || { echo "ERROR: Engine movie missing"; exit 1; }
	@test -f mod/DXP2/Movies/dark_crusade_intro.webm || { echo "ERROR: DXP2 movie missing"; exit 1; }
	@test -f mod/DXP3/Movies/soulstorm_intro.webm || { echo "ERROR: DXP3 movie missing"; exit 1; }
	@echo "✓ mod/ tree looks valid"

.PHONY: lint
lint: ## Ruff-lint the generator script (needs uv / ruff)
	uvx ruff check scripts/ 2>/dev/null || ruff check scripts/ 2>/dev/null || echo "note: ruff not installed, skipping"

.PHONY: clean
clean: ## Remove build artifacts
	rm -rf mod dist

.PHONY: dist
dist: build ## Alias for 'build'
