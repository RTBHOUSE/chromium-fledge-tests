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

HERE="$(cd "$(dirname "$0")"; pwd)"

DOWNLOADED_CHROMIUM_DIR="${HERE}/_chromium"

DOCKER_EXTRA_ARGS=()
GET_CHROMIUM_PARAMS=()
CHROMIUM_DIR=

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
  --chromium-url|--chromedriver-url|--chromium-revision)
    CHROMIUM_DIR=
    GET_CHROMIUM_PARAMS=("${GET_CHROMIUM_PARAMS[@]}" "$1" "$2")
    shift 2
    ;;
  --chromium-dir)
    CHROMIUM_DIR=`cd "$2"; pwd`
    shift 2
    ;;
  --downloaded)
    CHROMIUM_DIR=${DOWNLOADED_CHROMIUM_DIR}
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

if [[ -n ${CHROMIUM_DIR:-} ]]; then
  echo "using chromium build from local directory ${CHROMIUM_DIR}" >&2
else
  "${HERE}/get_chromium.sh" "${GET_CHROMIUM_PARAMS[@]}"
  CHROMIUM_DIR=${DOWNLOADED_CHROMIUM_DIR}
fi

[ -f "${CHROMIUM_DIR}/chromedriver" ] || { echo "chromium dir [${CHROMIUM_DIR}] does not contain chromedriver" >&2; exit 1; }

docker build --iidfile .iidfile -t chromium-fledge-tests "${HERE}" >&2

[ -t 0 ] && [ -t 1 ] && termOpt='-t' || termOpt=''

# container uses a different user
touch "${HERE}/chromedriver.log"
chmod a+w "${HERE}/chromedriver.log"

docker run --rm -i \
  ${termOpt} \
  -v "${CHROMIUM_DIR}:/home/usertd/chromium/" \
  -e CHROMIUM_DIR=/home/usertd/chromium \
  -e PROFILE_DIR=/home/usertd/profile \
  -v "${HERE}/chromedriver.log":/home/usertd/chromedriver.log \
  -e CHROMEDRIVER_LOG_PATH=/home/usertd/chromedriver.log \
  ${TEST_DIR:+-v "${TEST_DIR}:/home/usertd/tests/`basename "${TEST_DIR}"`"} \
  ${TEST:+-e TEST="$TEST"} \
  --shm-size=1gb \
  ${DOCKER_EXTRA_ARGS[@]+"${DOCKER_EXTRA_ARGS[@]}"} \
  "$(cat .iidfile)" \
  "$@"
