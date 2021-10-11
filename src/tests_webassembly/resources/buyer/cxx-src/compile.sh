#!/bin/bash
TARGET_JS_FILE=build/main.js

docker run -u "$(id -u):$(id -g)" -v "$(pwd):/src" --rm emscripten/emsdk \
  emcc --no-entry -O3 --closure 1 --no-entry functions.c -o build/functions.wasm

{
  cat << EOF
"use strict";
var performance;
if (typeof performance === 'undefined') {
    const perfHooks = require('perf_hooks');
    performance = perfHooks.performance;
}
const t_parse_start = performance.now();
EOF

  echo -n "const wasm_code = Uint8Array.from("
  python3 to_ints.py < build/functions.wasm

  echo ');'
  echo "const t_parse_end = performance.now();"
  cat < build/main.template.js

} > ${TARGET_JS_FILE}
