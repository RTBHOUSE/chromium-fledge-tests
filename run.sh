#!/bin/bash

# Usage:
# ./run.sh
#   [ --chromium-dir <path-to-chromium-dir> | --chromium-url <url-to-chromium-zip> ]
#   [ --test <module.Class.test_method> | <module> ]
#
# Examples:
# ./run.sh # runs all tests with official chrome build
# ./run.sh --test tests_functional.test.FunctionalTest.test__should_show_ad_our
# ./run.sh --test tests_functional.test
# ./run.sh --chromium-url https://github.com/RTBHOUSE/chromium/releases/download/94.0.4588.0-auction-timer/chromium.zip

set -euo pipefail
set -x

OPTIONS=
LONG_OPTIONS=chromium-dir:,chromium-url:,test:

CHROMIUM_DOWNLOADS="_chromium_downloads"
SKIP_BUILD="false"

PARSED=$(POSIXLY_CORRECT=1 getopt --options=$OPTIONS --longoptions=${LONG_OPTIONS} --name "$0" -- "$@")
if [[ $? -ne 0 ]]; then
  # getopt has complained about wrong arguments to stdout
  exit 2
fi

# read getopt’s output this way to handle the quoting right:
eval set -- "$PARSED"

# process options until we see --
while true; do
  case "$1" in
  --chromium-dir)
    CHROMIUM_DIR="$2"
    shift 2
    ;;
  --chromium-url)
    CHROMIUM_URL="$2"
    shift 2
    ;;
  --test)
    TEST="$2"
    shift 2
    ;;
  --)
    shift
    break
    ;;
  *)
    echo "Programming error, found ${1}"
    exit 1
    ;;
  esac
done

function downloadIfNotExists() {
  URL=$1
  LOCAL_PATH=$2
  if [ -f "${LOCAL_PATH}" ]; then
    echo "file exists (skip downloading): ${LOCAL_PATH}"
  else
    curl -L -# "${URL}" > "${LOCAL_PATH}"
  fi
}

function downloadChromiumWithDriver() {
    CHROMIUM_URL=$1
    CHROMIUM_ZIP_FILENAME=$2
    CHROMEDRIVER_URL=$3
    CHROMEDRIVER_ZIP_FILENAME=$4

    rm -rf "_chromium"
    mkdir -p "_chromium"
    mkdir -p ${CHROMIUM_DOWNLOADS}

    CHROMIUM_ZIP="${CHROMIUM_DOWNLOADS}/${CHROMIUM_ZIP_FILENAME}"
    downloadIfNotExists ${CHROMIUM_URL} ${CHROMIUM_ZIP}
    unzip "${CHROMIUM_ZIP}" -d "_chromium/chromium"

    CHROMIUM_PATH=$(find "${PWD}/_chromium/chromium/" -name chrome -type f)
    CHROMIUM_DIR=$(dirname "${CHROMIUM_PATH}")

    if [ ! -z "${CHROMEDRIVER_URL}" ]; then
      CHROMEDRIVER_ZIP="${CHROMIUM_DOWNLOADS}/${CHROMEDRIVER_ZIP_FILENAME}"
      downloadIfNotExists ${CHROMEDRIVER_URL} ${CHROMEDRIVER_ZIP}
      unzip "${CHROMEDRIVER_ZIP}" -d "_chromium/chromedriver"
      CHROMEDRIVER_PATH=$(find "${PWD}/_chromium/chromedriver/" -name chromedriver -type f)
      mv ${CHROMEDRIVER_PATH} "${CHROMIUM_DIR}/chromedriver"
    fi

    CHROMIUM_PATH=$(find "${PWD}/_chromium/chromium/" -name chrome -type f)
    CHROMIUM_DIR=$(dirname "${CHROMIUM_PATH}")
}

if [[ -n ${CHROMIUM_DIR:-} ]]; then
  if [[ ! ${CHROMIUM_DIR} == /* ]]; then
    echo "chromium directory must be an absolute path!"
    exit 1
  fi
  echo "using chromium build from local directory ${CHROMIUM_DIR}"
elif [[ -n ${CHROMIUM_URL:-} ]]; then
  echo "using chromium build from URL ${CHROMIUM_URL}"
  downloadChromiumWithDriver ${CHROMIUM_URL} $(basename ${CHROMIUM_URL})
else
  REVISION=$(curl -s -S 'https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2FLAST_CHANGE?alt=media')
  echo "using official chrome build (REVISION: ${REVISION})"

  CHROMIUM_URL="https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F${REVISION}%2Fchrome-linux.zip?alt=media"
  CHROMIUM_ZIP_NAME="chromium_rev_${REVISION}.zip"
  CHROMEDRIVER_URL="https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F${REVISION}%2Fchromedriver_linux64.zip?alt=media"
  CHROMEDRIVER_ZIP_NAME="chromedriver_rev_${REVISION}.zip"

  downloadChromiumWithDriver ${CHROMIUM_URL} ${CHROMIUM_ZIP_NAME} ${CHROMEDRIVER_URL} ${CHROMEDRIVER_ZIP_NAME}
fi

[ -f "${CHROMIUM_DIR}/chromedriver" ] || { echo "chromium dir [${CHROMIUM_DIR}] does not contain chromedriver"; exit 1; }

docker build --iidfile .iidfile -t chromium-fledge-tests . &> /dev/null

[ -t 0 ] && [ -t 1 ] && termOpt='-t' || termOpt=''

docker run --rm -i \
  ${termOpt} \
  -v "${CHROMIUM_DIR}:/home/usertd/chromium/" \
  -e TEST="$TEST" \
  --shm-size=1gb \
  --add-host fledge-tests.creativecdn.net:127.0.0.1 \
  "$(cat .iidfile)" \
  "$@"
