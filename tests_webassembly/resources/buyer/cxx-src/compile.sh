#!/bin/bash
TARGET_JS_FILE=build/main.js

docker run -u "$(id -u):$(id -g)" -v "$(pwd):/src" --rm emscripten/emsdk \
  emcc --no-entry -O3 --closure 1 --no-entry functions.c -o build/functions.wasm
#  emcc --no-entry -O3 -msimd128 --closure 1 --no-entry functions.c -o build/functions.wasm
# -fsanitize=undefined -g

cat << EOF > ${TARGET_JS_FILE}
"use strict";
var performance;
if (typeof performance === 'undefined') {
    const perfHooks = require('perf_hooks');
    performance = perfHooks.performance;
}
const t_start = performance.now();
EOF

echo -n "const wasm_code = Uint8Array.from(" >> ${TARGET_JS_FILE}
#echo -n "const wasm_code =\"" >> ${TARGET_JS_FILE}
python3 to_ints.py < build/functions.wasm >> ${TARGET_JS_FILE}
echo ');' >> ${TARGET_JS_FILE}
#base64 -w0 < build/functions.wasm >> ${TARGET_JS_FILE}
#echo '";' >> ${TARGET_JS_FILE}
cat < build/main.template.js >> ${TARGET_JS_FILE}



