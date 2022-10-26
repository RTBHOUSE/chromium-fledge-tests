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
LONG_OPTIONS=chromium-dir:,chromium-url:,chromedriver-url:,chromium-revision:,downloaded,test:,test-dir:,gui

CHROMIUM_DOWNLOADS="_chromium_downloads"
UNPACK_DIR="_chromium"

DOCKER_EXTRA_ARGS=()
REVISION=latest

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
  --chromium-dir)
    CHROMIUM_DIR=`cd "$2"; pwd`
    shift 2
    ;;
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
  --downloaded)
    CHROMIUM_DIR=$(find "${HERE}/${UNPACK_DIR}/chromium/" -name chrome -type f -exec dirname {} \;)
    shift 1
    ;;
  --test)
    TEST="$2"
    shift 2
    ;;
  --test-dir)
    TEST_DIR=`cd "$2"; pwd`
    TEST="discover -s $(basename "${TEST_DIR}")"
    shift 2
    ;;
  --gui)
    DOCKER_EXTRA_ARGS=("${DOCKER_EXTRA_ARGS[@]}"
      -e DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix -e "XAUTH=`xauth list $DISPLAY`"
    )
    shift
    ;;
  --)
    # Non-option arguments are passed to docker container as a command
    # You can also pass extra docker-run parameters after --:
    #  run.sh [usual run.sh parameters] -- [docker-run parameters]
    #  run.sh [usual run.sh parameters] -- [docker-run parameters] -- [container command]
    #  run.sh [usual run.sh parameters] [container command]
    shift
    if [[ "${1:-}" = -* ]]; then
      for ((i=1; i <= $#; i++)); do
        [ "${!i}" == "--" ] && break
      done
      DOCKER_EXTRA_ARGS=("${DOCKER_EXTRA_ARGS[@]}" "${@:1:i}")
      set -- "${@:i+1}"
    fi
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

    rm -rf "${UNPACK_DIR}"
    mkdir -p "${UNPACK_DIR}"
    mkdir -p "${CHROMIUM_DOWNLOADS}"

    CHROMIUM_FILE_PATH="${CHROMIUM_DOWNLOADS}/${CHROMIUM_FILENAME:-${CHROMIUM_URL//\//_}}"
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

    CHROMIUM_DIR=$(find "${PWD}/${UNPACK_DIR}/chromium/" -name chrome -type f -exec dirname {} \;)

    if [ ! -z "${CHROMEDRIVER_URL}" ]; then
      CHROMEDRIVER_ZIP="${CHROMIUM_DOWNLOADS}/${CHROMEDRIVER_ZIP_FILENAME:-${CHROMEDRIVER_URL//\//_}}"
      downloadIfOutdated ${CHROMEDRIVER_URL} ${CHROMEDRIVER_ZIP}
      unzip "${CHROMEDRIVER_ZIP}" -d "${UNPACK_DIR}/chromedriver/" >&2
      CHROMEDRIVER_PATH=$(find "${PWD}/${UNPACK_DIR}/chromedriver/" -name chromedriver -type f)
      mv ${CHROMEDRIVER_PATH} "${CHROMIUM_DIR}/chromedriver"
    fi
}

if [[ -n ${CHROMIUM_DIR:-} ]]; then
  echo "using chromium build from local directory ${CHROMIUM_DIR}" >&2
elif [[ -n ${CHROMIUM_URL:-} ]]; then
  echo "using chromium build from URL ${CHROMIUM_URL}" >&2
  downloadChromiumWithDriver "${CHROMIUM_URL}" "" "${CHROMEDRIVER_URL:+${CHROMEDRIVER_URL}}" ""
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

[ -f "${CHROMIUM_DIR}/chromedriver" ] || { echo "chromium dir [${CHROMIUM_DIR}] does not contain chromedriver" >&2; exit 1; }

docker build --iidfile .iidfile -t chromium-fledge-tests . &> /dev/null

[ -t 0 ] && [ -t 1 ] && termOpt='-t' || termOpt=''

docker run --rm -i \
  ${termOpt} \
  -v "${CHROMIUM_DIR}:/home/usertd/chromium/" \
  ${TEST_DIR:+-v "${TEST_DIR}:/home/usertd/tests/`basename "${TEST_DIR}"`"} \
  ${TEST:+-e TEST="$TEST"} \
  --shm-size=1gb \
  --add-host fledge-tests.creativecdn.net:127.0.0.1 \
  ${DOCKER_EXTRA_ARGS[@]+"${DOCKER_EXTRA_ARGS[@]}"} \
  "$(cat .iidfile)" \
  "$@"
