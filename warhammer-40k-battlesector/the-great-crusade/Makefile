# The Great Crusade — build Makefile
#
# One tuned config (parameters live as code in build.py: LEVEL_CAP, STEP,
# rarity curve). Upgrade-card EFFECT values live in the hand-editable cards.json
# and are applied on every build. This Makefile selects which base to build:
#   standalone  built on the vanilla startup_assets_all.bundle
#   tccompat    built on the Traditional Chinese localization bundle (keeps TC fonts)
#
# Card effects:
#   Edit cards.json / cards-nonplayer.json by hand, then `make` to bake the values
#   into the zips. `make export-cards` regenerates the card files from the vanilla
#   bundle (won't overwrite existing hand-edited files; use FORCE=1) and always
#   refreshes the read-only cards-vanilla.json reference (all 55 vanilla values).
#
# Requirements: Python with UnityPy (see README). Override PYTHON if needed, e.g.
#   make all PYTHON=/path/to/venv/bin/python
#
# Vanilla base: set BS_VANILLA_BUNDLE (or BS_GAME_DIR) to a pristine bundle.
# See README "Build inputs".

PYTHON ?= ../../.copilot_workspace/battlesector-data/venv/bin/python
BUILD  := $(PYTHON) build.py
FORCE  ?=

.PHONY: all standalone tccompat export-cards cost-policy clean

all: standalone tccompat

standalone:
	$(BUILD) standalone

tccompat:
	$(BUILD) tccompat

export-cards:
	$(BUILD) export-cards $(if $(FORCE),--force,)

cost-policy:
	$(BUILD) cost-policy

clean:
	rm -rf .copilot_workspace/stage
	rm -f dist/the-great-crusade*.zip
