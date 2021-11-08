#!/bin/bash
set -x
set -euo pipefail
cd $(readlink -f $(dirname "$0"))

(
    cd cxx-src
    docker run -u "$(id -u):$(id -g)" -v "$(pwd):/src" --rm emscripten/emsdk \
      emcc --no-entry -O3 --closure 1 --no-entry functions.c -o build/functions.wasm
)

python3 -c '
import jinja2
import json

wasm_code = open("cxx-src/build/functions.wasm", "rb").read()
wasm_str = [int(c) for c in wasm_code]

jenv = jinja2.Environment(loader=jinja2.FileSystemLoader("."))

tmpl_chromium = jenv.from_string(open("buyer-chromium.template.js").read())
open("buyer-chromium.js", "w").write(tmpl_chromium.render(wasm_code=json.dumps(wasm_str)))

tmpl_v8 = jenv.from_string(open("buyer-v8.template.js").read())
open("buyer-v8.js", "w").write(tmpl_v8.render(wasm_code=json.dumps(wasm_str)))
'
