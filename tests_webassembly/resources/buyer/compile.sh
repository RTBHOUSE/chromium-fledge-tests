#!/bin/bash
TARGET_JS_FILE=buyer.js

cd cxx-src && bash ./compile.sh
cd ..

{
  echo '"use strict";'
  echo -n "const wasm_code = Uint8Array.from("
  python3 cxx-src/to_ints.py < cxx-src/build/functions.wasm
  echo ');'
  cat < buyer.template.js
} > ${TARGET_JS_FILE}


