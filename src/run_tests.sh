#!/bin/bash

if [[ -z TEST_LIB_DIR ]] && [[ -n "${TEST_LIB_DIR}" ]]; then
  export PYTHONPATH="${TEST_LIB_DIR}:${PYTHONPATH}"
fi

python3 -m unittest $TEST --verbose
