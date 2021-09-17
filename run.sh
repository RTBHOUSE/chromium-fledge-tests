#!/bin/bash

# Usage:
# ./run.sh
#   [ --chromium-directory <path-to-chromium-dir> | --chromium-url <url-to-chromium-zip> ]
#   [ --test <module.Class.test_method> ]
#
# Examples:
# ./run.sh # runs all tests with official chrome build
# ./run.sh --test tests_functional.test.FunctionalTest.test__should_show_ad_our
# ./run.sh --chromium-url https://github.com/RTBHOUSE/chromium/releases/download/94.0.4588.0-auction-timer/chromium.zip

set -e

OPTIONS=
LONG_OPTIONS=chromium-directory:,chromium-url:,test:

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
  --chromium-directory)
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

if [[ -n ${CHROMIUM_DIR} ]]; then
  if [[ ! ${CHROMIUM_DIR} == /* ]]; then
    echo "chromium directory must be an absolute path!"
    exit 1
  fi
  echo "using chromium build from local directory ${CHROMIUM_DIR}"
  volumeOpt="-v ${CHROMIUM_DIR}:/home/usertd/chromium-custom/"
elif [[ -n ${CHROMIUM_URL} ]]; then
  echo "using chromium build from URL ${CHROMIUM_URL}"
  mkdir -p "_chromium"
  cd "_chromium"
  curl -L -# "${CHROMIUM_URL}" > "chromium-custom.zip"
  unzip "chromium-custom.zip"
  CHROMIUM_PATH=$(find "${PWD}/" -name chrome -type f)
  CHROMIUM_DIR=$(dirname "${CHROMIUM_PATH}")
  volumeOpt="-v ${CHROMIUM_DIR}:/home/usertd/chromium-custom/"
  cd ../
else
  echo "using official chrome build"
  volumeOpt=""
fi

docker build --iidfile .iidfile .

[ -t 0 ] && [ -t 1 ] && termOpt='-t' || termOpt=''

docker run --rm -i \
  ${termOpt} \
  ${volumeOpt} \
  -e TEST="$TEST" \
  --shm-size=1gb \
  --add-host fledge-tests.creativecdn.net:127.0.0.1 \
  "$(cat .iidfile)" \
  "$@"
