#!/bin/bash

# Usage:
# ./get_chromium.sh
#   [ --chromium-url <url-to-chromium-zip-or-chrome-deb> | --chromium-revision <revision-number> | --chromium-channel <Stable|Beta|Dev|Canary> ]
#   [ --chromedriver-url <url-to-chromedriver-zip> ]  # optional, detected automatically
#
# Examples:
# ./get_chromium.sh # downloads latest Chromium snapshot
# ./get_chromium.sh --chromium-url https://github.com/RTBHOUSE/chromium/releases/download/94.0.4588.0-auction-timer/chromium.zip
# ./get_chromium.sh --chromium-channel Beta  # Download latest Beta for linux64



set -euo pipefail
set -x

OPTIONS=
LONG_OPTIONS=chromium-url:,chromedriver-url:,chromium-revision:,chromium-channel:

DOWNLOADS_DIR="_chromium_downloads"
UNPACK_DIR="_chromium_unpack"
CHROMIUM_DIR="_chromium"

REVISION=latest
CHROMIUM_CHANNEL=
PLATFORM="linux64"

PARSED=$(POSIXLY_CORRECT=1 getopt --options=$OPTIONS --longoptions=${LONG_OPTIONS} --name "$0" -- "$@")
if [[ $? -ne 0 ]]; then
  # getopt has complained about wrong arguments to stdout
  exit 2
fi

HERE="$(cd "$(dirname "$0")"; pwd)"

# read getopt’s output this way to handle the quoting right:
eval set -- "$PARSED"

# process options until we see --
while true; do
  case "$1" in
  --chromium-url)
    CHROMIUM_URL="$2"
    shift 2
    ;;
  --chromedriver-url)
    CHROMEDRIVER_URL="$2"
    shift 2
    ;;
  --chromium-revision)
    REVISION="$2"
    shift 2
    ;;
  --chromium-channel)
    CHROMIUM_CHANNEL="$2"
    shift 2
    ;;
  --)
    shift
    break
    ;;
  *)
    echo "Programming error, found ${1}" >&2
    exit 1
    ;;
  esac
done

cd "${HERE}"

function fetchVersion() {
  local url=$1
  curl -s -S "${url}" | egrep '^[0-9.]+$'
}

function downloadIfOutdated() {
  URL=$1
  LOCAL_PATH=$2
  if [ -f "${LOCAL_PATH}" ]; then
    curl --location --progress-bar --output "${LOCAL_PATH}" "${URL}" --time-cond "${LOCAL_PATH}"
  else
    curl --location --progress-bar --output "${LOCAL_PATH}" "${URL}"
  fi
}

function downloadChromiumWithDriver() {
    CHROMIUM_URL=$1
    CHROMIUM_FILENAME=${2:-}
    CHROMEDRIVER_URL=${3:-}
    CHROMEDRIVER_ZIP_FILENAME=${4:-}

    rm -rf "${UNPACK_DIR}" "${CHROMIUM_DIR}"
    mkdir -p "${UNPACK_DIR}"
    mkdir -p "${DOWNLOADS_DIR}"

    CHROMIUM_FILE_PATH="${DOWNLOADS_DIR}/${CHROMIUM_FILENAME:-${CHROMIUM_URL//\//_}}"
    downloadIfOutdated ${CHROMIUM_URL} ${CHROMIUM_FILE_PATH}
    if [[ "${CHROMIUM_FILE_PATH}" = *.deb ]]; then
      if [[ -z "${CHROMEDRIVER_URL}" ]]; then
        # https://chromedriver.chromium.org/downloads/version-selection
        DEB_VERSION=`dpkg -f "${CHROMIUM_FILE_PATH}" Version`
        UP_TO_LAST_DOT_VERSION=${DEB_VERSION%.*-*}
        MAJOR_VERSION=${DEB_VERSION%%.*}
        if CHROMEDRIVER_VERSION=$(fetchVersion "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${UP_TO_LAST_DOT_VERSION}") ||
            CHROMEDRIVER_VERSION=$(fetchVersion "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${MAJOR_VERSION}") ||
            CHROMEDRIVER_VERSION=$(fetchVersion "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$[MAJOR_VERSION-1]"); then
          CHROMEDRIVER_URL="https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
        fi
      fi
      dpkg -x "${CHROMIUM_FILE_PATH}" "${UNPACK_DIR}/chromium/" >&2
    else
      unzip "${CHROMIUM_FILE_PATH}" -d "${UNPACK_DIR}/chromium/" >&2
    fi

    CHROME_PATH=$(find "${UNPACK_DIR}/chromium/" -name chrome -type f -exec dirname {} \;)

    if [ -z "${CHROME_PATH}" ]; then
      echo "chould not find 'chrome' binary in ${UNPACK_DIR} after extracting downloaded file" >&2
      exit 1
    fi

    mv "${CHROME_PATH}" ${CHROMIUM_DIR}

    if [ ! -z "${CHROMEDRIVER_URL}" ]; then
      CHROMEDRIVER_ZIP="${DOWNLOADS_DIR}/${CHROMEDRIVER_ZIP_FILENAME:-${CHROMEDRIVER_URL//\//_}}"
      downloadIfOutdated ${CHROMEDRIVER_URL} ${CHROMEDRIVER_ZIP}
      unzip "${CHROMEDRIVER_ZIP}" -d "${UNPACK_DIR}/chromedriver/" >&2

      CHROMEDRIVER_PATH=$(find "${UNPACK_DIR}/chromedriver/" -name chromedriver -type f)
      if [ -z "${CHROMEDRIVER_PATH}" ]; then
        echo "chould not find 'chromedriver' binary in ${UNPACK_DIR} after extracting downloaded file" >&2
        exit 1
      fi
      mv ${CHROMEDRIVER_PATH} "${CHROMIUM_DIR}/chromedriver"
    fi

    echo "Downloaded ${CHROMIUM_URL} and extracted to ${PWD}/${CHROMIUM_DIR}" >&2
}

function downloadChromeForTesting() {
  JQ=$(which jq 2>/dev/null || echo "docker run --rm -i --name chromium-fledge-tests-jq-${RANDOM} ghcr.io/jqlang/jq:latest")

  LATEST_CHROMIUM_FOR_TESTING="https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
  CHROMIUM_JSON=$(curl ${LATEST_CHROMIUM_FOR_TESTING})
  CHROMIUM_URL=$(echo ${CHROMIUM_JSON} | $JQ -r ".channels.${CHROMIUM_CHANNEL}.downloads.chrome[] | select(.platform == \"${PLATFORM}\") | .url")
  CHROMEDRIVER_URL=$(echo ${CHROMIUM_JSON} | $JQ -r ".channels.${CHROMIUM_CHANNEL}.downloads.chromedriver[] | select(.platform == \"${PLATFORM}\") | .url")

  downloadChromiumWithDriver "${CHROMIUM_URL}" "" "${CHROMEDRIVER_URL}" ""
}

if [[ -n ${CHROMIUM_URL:-} ]]; then
  echo "using chromium build from URL ${CHROMIUM_URL}" >&2
  downloadChromiumWithDriver "${CHROMIUM_URL}" "" "${CHROMEDRIVER_URL:+${CHROMEDRIVER_URL}}" ""
elif [[ -n ${CHROMIUM_CHANNEL:-} ]]; then
  if ! [[ "$CHROMIUM_CHANNEL" =~ ^(Stable|Beta|Dev|Canary)$ ]]; then
    echo "invalid channel value: ${CHROMIUM_CHANNEL}" >&2
    exit 1
  fi
  echo "using chrome for testing channel ${CHROMIUM_CHANNEL}" >&2
  downloadChromeForTesting
else
  if [[ "${REVISION}" == latest ]]; then
    REVISION=$(fetchVersion 'https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2FLAST_CHANGE?alt=media')
    echo "using latest chromium snapshot build (REVISION: ${REVISION})" >&2
  else
    echo "using chromium snapshot build (REVISION: ${REVISION})" >&2
  fi

  CHROMIUM_URL="https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F${REVISION}%2Fchrome-linux.zip?alt=media"
  CHROMIUM_ZIP_NAME="chromium_rev_${REVISION}.zip"
  CHROMEDRIVER_URL="https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F${REVISION}%2Fchromedriver_linux64.zip?alt=media"
  CHROMEDRIVER_ZIP_NAME="chromedriver_rev_${REVISION}.zip"

  downloadChromiumWithDriver ${CHROMIUM_URL} ${CHROMIUM_ZIP_NAME} ${CHROMEDRIVER_URL} ${CHROMEDRIVER_ZIP_NAME}
fi
