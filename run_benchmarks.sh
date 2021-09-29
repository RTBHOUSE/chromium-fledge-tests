#!/bin/bash

echo "### benchmark 1: tight loop with a warm-up run in V8 engine with jit"
docker run --rm -it -v $PWD/tests_performance:/tests_performance/ andreburgaud/d8 \
  /tests_performance/resources/benchmark.js

echo "### benchmark 2: buyer's js run as a bidding worklet in Chromium"
bash run.sh --test tests_performance.test \
  --chromium-url https://github.com/RTBHOUSE/chromium/releases/download/94.0.4588.0-auction-timer/chromium.zip

echo "### benchmark 3: buyer’s js without warm-up run in V8 engine"
docker run --rm -it -v $PWD/tests_performance:/tests_performance/ andreburgaud/d8 \
  /tests_performance/resources/benchmark.js --jitless --optimize_for_size --no-expose-wasm

echo "### benchmark 4: buyer’s js with wasm binary but without warm-up run in V8 engine"
cd tests_webassembly/resources/buyer/cxx-src
bash compile.sh
cd ../../../../
docker run --rm -it -v $PWD/tests_webassembly:/tests_webassembly/ andreburgaud/d8 \
  /tests_webassembly/resources/buyer/cxx-src/build/main.js --optimize_for_size

echo "### benchmark 5: buyer’s js with wasm binary run as a bidding worklet in Chromium"
bash run.sh --test tests_webassembly.test \
  --chromium-url https://github.com/RTBHOUSE/chromium/releases/download/96.0.4644.0-async-5000ms-wasm/chromium-webassembly.zip
