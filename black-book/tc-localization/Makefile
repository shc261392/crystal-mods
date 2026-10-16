.PHONY: help build generate build-plugin validate package check-package clean install uninstall

# ============================================================================
# Black Book TC Localization Mod — Build System
#
# ONE canonical release command:
#
#     make build
#
# It regenerates the payload from the checked-in SC source, compiles the
# BepInEx plugin, runs every quality gate, and packages the release zip. No
# arguments, no overrides, no alternate recipes (AGENTS.md rule 15).
#
# The Unity-built font bundle (plugin/bundles/tcserif) is a committed artifact:
# TMP font assets cannot be produced without the Unity Editor. Regenerate it
# with tools/unity-font/ - see its README.
# ============================================================================

SHELL       := /bin/bash
PYTHON      ?= python3
MOD_DIR     := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
SCRIPTS_DIR := $(MOD_DIR)/scripts
DIST_DIR    := $(MOD_DIR)/dist
PAYLOAD_DIR := $(MOD_DIR)/payload

MOD_VERSION := 1.3.0
MOD_ZIP     := tc-localization-v$(MOD_VERSION).zip

GATES := gate_coverage gate_structure gate_simplified gate_overrides gate_terminology

help:
	@echo "Black Book TC Localization Mod"
	@echo ""
	@echo "  make build         - generate + compile plugin + validate + package"
	@echo "  make generate      - SC source -> TC payload"
	@echo "  make build-plugin  - compile the BepInEx plugin"
	@echo "  make validate      - run all quality gates"
	@echo "  make check-package - confirm the build is reproducible"
	@echo "  make install       - deploy to the game (runs deploy.sh)"
	@echo "  make uninstall     - restore the game (runs uninstall.sh)"
	@echo "  make clean         - remove generated payload, plugin output and dist"
	@echo ""

# ---------------------------------------------------------------------------
# The release build. Nothing else produces the release zip.
# ---------------------------------------------------------------------------
build: generate build-plugin validate package
	@echo ""
	@echo "Build complete: dist/$(MOD_ZIP)"

# ---------------------------------------------------------------------------
generate:
	@echo "==> Generating TC payload from source/sc"
	@$(PYTHON) $(SCRIPTS_DIR)/build_tc_payload.py

# ---------------------------------------------------------------------------
build-plugin:
	@echo "==> Compiling the BepInEx plugin"
	@bash $(MOD_DIR)/build_plugin.sh

# ---------------------------------------------------------------------------
validate:
	@echo "==> Running quality gates"
	@for gate in $(GATES); do \
		$(PYTHON) $(SCRIPTS_DIR)/$$gate.py || exit 1; \
	done
	@echo ""

# ---------------------------------------------------------------------------
package:
	@echo "==> Packaging"
	@$(PYTHON) $(SCRIPTS_DIR)/package_zip.py \
		--payload "$(PAYLOAD_DIR)" \
		--stage "$(DIST_DIR)/stage" \
		--dist "$(DIST_DIR)" \
		--name "$(MOD_ZIP)"

# ---------------------------------------------------------------------------
check-package:
	@echo "==> Verifying the build is reproducible"
	@$(PYTHON) $(SCRIPTS_DIR)/check_reproducible.py \
		--dist "$(DIST_DIR)" --name "$(MOD_ZIP)"

# ---------------------------------------------------------------------------
clean:
	@rm -rf "$(PAYLOAD_DIR)" "$(DIST_DIR)"
	@rm -rf $(MOD_DIR)/plugin/bin $(MOD_DIR)/plugin/obj
	@rm -rf $(MOD_DIR)/scripts/__pycache__
	@echo "Cleaned generated payload, plugin output and dist/"

install: build
	@bash $(MOD_DIR)/deploy.sh

uninstall:
	@bash $(MOD_DIR)/uninstall.sh