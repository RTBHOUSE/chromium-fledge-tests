#!/bin/bash

set -vx
echo "(1) hello from chromium-fledge-tests/src/run_tests.sh; PYTHONPATH=$PYTHONPATH"
pwd
ls -la

if [[ -z TEST_LIB_DIR ]] && [[ -n "${TEST_LIB_DIR}" ]]; then
  export PYTHONPATH="${TEST_LIB_DIR}:${PYTHONPATH}"
fi

echo "(2) hello from chromium-fledge-tests/src/run_tests.sh; PYTHONPATH=$PYTHONPATH"
python3 -m unittest $TEST --verbose
