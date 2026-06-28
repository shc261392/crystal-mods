#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="${ROOT}/.copilot_workspace/vortex-font-profiles"
ARCHIVE_EXE="${ARCHIVE_EXE:-/mnt/d/SteamLibrary/steamapps/common/Dawn of War Definitive Edition/Archive.exe}"
BASELINE_JSON="${ROOT}/reference/font_size_baseline.json"
VERSION="$(python3 -c "import json, pathlib; print(json.loads(pathlib.Path('${ROOT}/modinfo.json').read_text())['version'])")"
PKG_NAME="wh40k-dow-de-tc-mod-v${VERSION}-vortex"
DIST_ZIP="${ROOT}/dist/${PKG_NAME}.zip"
DEFAULT_SIZE="${DEFAULT_SIZE:-36}"
SIZE_4K="${SIZE_4K:-38}"

BASE_SGA="${ROOT}/EnginLocMod.sga"
BASE_UCS="${ROOT}/Engine.ucs"

[[ -f "${ARCHIVE_EXE}" ]] || { echo "Archive.exe not found: ${ARCHIVE_EXE}"; exit 1; }
[[ -f "${BASE_SGA}" ]] || { echo "Base SGA not found: ${BASE_SGA}"; exit 1; }
[[ -f "${BASE_UCS}" ]] || { echo "Engine.ucs not found: ${BASE_UCS}"; exit 1; }

rm -rf "${WORK_DIR}" "${DIST_ZIP}"
mkdir -p "${WORK_DIR}/source_extract" "${WORK_DIR}/build"

"${ARCHIVE_EXE}" -a "${BASE_SGA}" -e "${WORK_DIR}/source_extract" >/dev/null

make_buildfile() {
  local build_file="$1"
  cat > "${build_file}" <<'EOF'
Archive
TOCStart alias="data" relativeroot="."
FileSettingsStart defcompression="1"
    Override wildcard=".*(gfx)$" minsize="-1" maxsize="-1" ct="1"
    Override wildcard=".*(fnt)$" minsize="-1" maxsize="-1" ct="2"
    Override wildcard=".*(ttf|ttc)$" minsize="-1" maxsize="-1" ct="0"
    Override wildcard=".*(fda|rat)$" minsize="-1" maxsize="-1" ct="2"
FileSettingsEnd
TOCEnd
EOF
  sed -i 's/$/\r/' "${build_file}"
}

build_profile() {
  local profile_name="$1"
  local target_size="$2"
  local folder_name="$3"
  local extract_dir="${WORK_DIR}/${folder_name}-extract"
  local option_dir="${WORK_DIR}/build/${folder_name}/Engine/Locale/Chinese"
  local build_file="${WORK_DIR}/${folder_name}.txt"

  rm -rf "${extract_dir}" "${WORK_DIR}/build/${folder_name}"
  cp -a "${WORK_DIR}/source_extract" "${extract_dir}"

  if [[ "${profile_name}" == "vanilla" ]]; then
    python3 "${ROOT}/scripts/apply_font_profile.py" \
      --font-dir "${extract_dir}/font" \
      --baseline "${BASELINE_JSON}" \
      --profile vanilla
  else
    python3 "${ROOT}/scripts/apply_font_profile.py" \
      --font-dir "${extract_dir}/font" \
      --baseline "${BASELINE_JSON}" \
      --profile "${profile_name}" \
      --size-default "${target_size}"
  fi

  mkdir -p "${option_dir}"
  make_buildfile "${build_file}"
  "${ARCHIVE_EXE}" -c "${build_file}" -r "${extract_dir}" -a "${option_dir}/EnginLoc.sga" >/dev/null
  cp "${BASE_UCS}" "${option_dir}/Engine.ucs"
}

build_profile vanilla 0 "00-vanilla"
build_profile 1080p "${DEFAULT_SIZE}" "01-1080p-plus"
build_profile 4k "${SIZE_4K}" "02-4k-plus"

mkdir -p "${WORK_DIR}/build/fomod"
cp "${ROOT}/vortex-fomod/info.xml" "${WORK_DIR}/build/fomod/info.xml"
cp "${ROOT}/vortex-fomod/ModuleConfig.xml" "${WORK_DIR}/build/fomod/ModuleConfig.xml"

(
  cd "${WORK_DIR}/build"
  zip -r "${DIST_ZIP}" . -x "*.DS_Store"
)

echo "Built ${DIST_ZIP}"
ls -lh "${DIST_ZIP}"
