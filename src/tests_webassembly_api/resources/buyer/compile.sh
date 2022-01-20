#!/bin/bash
set -x
set -euo pipefail
cd $(readlink -f $(dirname "$0"))

(
    cd cxx-src
    docker run -u "$(id -u):$(id -g)" -v "$(pwd):/src" --rm emscripten/emsdk \
      emcc --no-entry -O3 --closure 1 --no-entry functions.c -o build/functions.wasm
)
