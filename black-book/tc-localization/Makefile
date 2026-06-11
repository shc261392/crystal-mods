.PHONY: build validate clean help install uninstall

# ============================================================================
# Black Book TC Localization Mod — Build System
# ============================================================================

SHELL := /bin/bash
PYTHON := python3
DIST_DIR := dist
PAYLOAD_DIR := payload
SCRIPTS_DIR := scripts
REFERENCE_DIR := reference

MOD_VERSION := 1.0.0
MOD_ZIP := tc-localization-v$(MOD_VERSION).zip

help:
	@echo "Black Book TC Localization Mod — Build Targets"
	@echo ""
	@echo "  make build      - Convert SC→TC, validate, package to $(DIST_DIR)/"
	@echo "  make validate   - Run quality gates on payload"
	@echo "  make clean      - Reset payload directory"
	@echo "  make install    - Deploy mod to game (requires ./deploy.sh or deploy.ps1)"
	@echo "  make help       - Show this help message"
	@echo ""

build: validate package
	@echo "✓ Build complete: $(DIST_DIR)/$(MOD_ZIP)"

validate:
	@echo "Running quality gates..."
	@echo ""
	@echo "[Gate 1] Checking YAML config structure..."
	@if [ -d "$(PAYLOAD_DIR)/Black Book_Data/StreamingAssets/Config" ]; then \
		YAML_COUNT=$$(find "$(PAYLOAD_DIR)/Black Book_Data/StreamingAssets/Config" -name "config_zh.yaml" | wc -l); \
		if [ $$YAML_COUNT -gt 0 ]; then \
			echo "[✓] Found $$YAML_COUNT TC config files"; \
		else \
			echo "[FAIL] No TC YAML config files found"; exit 1; \
		fi; \
	else \
		echo "[FAIL] TC config directory not found"; exit 1; \
	fi
	@echo ""
	@echo "[Gate 2] Validating YAML format..."
	@$(PYTHON) $(SCRIPTS_DIR)/gate0_yaml_validator.py || exit 1
	@echo ""
	@echo "[Gate 3] Font asset validation (optional)..."
	@if [ -d "$(PAYLOAD_DIR)/Fonts" ]; then \
		FONT_COUNT=$$(find "$(PAYLOAD_DIR)/Fonts" -type f | wc -l); \
		echo "[✓] Found $$FONT_COUNT font files"; \
	else \
		echo "[ℹ] No font files (optional for initial release)"; \
	fi
	@echo ""
	@echo "✓ All validation gates passed"

package:
	@echo "Packaging mod..."
	@mkdir -p $(DIST_DIR)
	@cd $(PAYLOAD_DIR) && zip -r ../$(DIST_DIR)/$(MOD_ZIP) . -x "*.git*" "*.DS_Store"
	@echo "✓ Packaged to: $(DIST_DIR)/$(MOD_ZIP)"

convert-sc-to-tc:
	@echo "Extracting SC YAML configs and converting to TC..."
	@$(PYTHON) $(SCRIPTS_DIR)/extract_and_convert_yaml.py || exit 1
	@echo "✓ Conversion complete"

clean:
	@echo "Cleaning payload..."
	@rm -rf $(PAYLOAD_DIR)/Black\ Book_Data/StreamingAssets/Config/
	@rm -rf $(DIST_DIR)
	@rm -f $(PAYLOAD_DIR)/EXTRACTION_REPORT.txt
	@echo "✓ Cleaned"

install: build
	@echo "Installing mod..."
	@bash deploy.sh

uninstall:
	@echo "Uninstalling mod..."
	@bash uninstall.sh

# ============================================================================
# Development targets
# ============================================================================

.PHONY: glossary format-terminology

glossary:
	@echo "Opening terminology glossary..."
	@cat $(REFERENCE_DIR)/TERMINOLOGY.md

format-terminology:
	@echo "Formatting terminology file..."
	@$(PYTHON) $(SCRIPTS_DIR)/normalize_glossary.py $(REFERENCE_DIR)/TERMINOLOGY.md
	@echo "✓ Terminology formatted"

# ============================================================================
# Continuous Integration targets (for CI/CD pipelines)
# ============================================================================

.PHONY: ci-validate ci-build

ci-validate: validate
	@echo "✓ CI validation passed"

ci-build: ci-validate package
	@echo "✓ CI build passed"
