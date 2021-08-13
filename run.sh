#!/bin/bash

# Usage:
#  ./run.sh  # runs tests with official chrome build
#  ./run.sh --chromium-directory <path-to-chromium-dir>
#  ./run.sh --chromium-url <url-to-chromium-zip>

set -e

OPTIONS=
LONG_OPTIONS=chromium-directory:,chromium-url:

PARSED=$(getopt --options=$OPTIONS --longoptions=${LONG_OPTIONS} --name "$0" -- "$@")
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

if [[ $# -ne 0 ]]; then
  echo "$0: There is some options unprocessed $@"
  exit 1
fi


if [[ -n ${CHROMIUM_DIR} ]]; then
  if [[ ! ${CHROMIUM_DIR} == /* ]]; then
    echo "chromium directory must be an absolute path!"
    exit 1
  fi
  echo "using chromium build from local directory ${CHROMIUM_DIR}"
  volumeOpt="-v ${CHROMIUM_DIR}:/home/usertd/chromium-custom/"
elif [[ -n ${CHROMIUM_URL} ]]; then
  echo "using chromium build from URL ${CHROMIUM_URL}"
  mkdir -p "extracted"
  cd "extracted"
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
docker run --rm -i ${termOpt} ${volumeOpt} --shm-size=1gb --add-host fledge-tests.creativecdn.net:127.0.0.1 "$(cat .iidfile)" "$@"
