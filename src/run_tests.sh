#!/bin/bash

set -vx
echo "hello from chromium-fledge-tests/src/run_tests.sh"
pwd
ls -laR
python3 -m unittest $TEST --verbose
