#!/bin/bash

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <benchmark>"
  exit 2
fi
BENCHMARK=$1

if [ $BENCHMARK == 1 ]; then
  echo "### benchmark 1: tight loop with a warm-up run in V8 engine with jit"
  docker run --rm -it -v $PWD/src/tests_performance:/tests_performance/ andreburgaud/d8 /tests_performance/resources/benchmark.js
elif [ $BENCHMARK == 2 ]; then
  echo "### benchmark 2: buyer's js run as a bidding worklet in Chromium"
  bash run.sh --test tests_performance.test \
    --chromium-url https://github.com/RTBHOUSE/chromium/releases/download/96.0.4644.0-5000ms-auction-timer/chromium-bid_duration_5s.zip
elif [ $BENCHMARK == 3 ]; then
  echo "### benchmark 3: buyer’s js without warm-up run in V8 engine"
  docker run --rm -it -v $PWD/src/tests_performance:/tests_performance/ andreburgaud/d8 /tests_performance/resources/benchmark.js --jitless --optimize_for_size --no-expose-wasm
elif [ $BENCHMARK == 4 ]; then
  echo "### benchmark 4: buyer’s js with wasm binary but without warm-up run in V8 engine"
  cd src/tests_webassembly/resources/buyer/cxx-src; bash compile.sh; cd ../../../../../
  docker run --rm -it -v $PWD/src/tests_webassembly:/tests_webassembly/ andreburgaud/d8 /tests_webassembly/resources/buyer/cxx-src/build/main.js --optimize_for_size
elif [ $BENCHMARK == 5 ]; then
  echo "### benchmark 5: buyer’s js with wasm binary run as a bidding worklet in Chromium"
  bash run.sh --test tests_webassembly.test \
    --chromium-url https://github.com/RTBHOUSE/chromium/releases/download/96.0.4651.0-5000ms-wasm-auction-timer/chromium-wasm.zip
else
  echo "unknown benchmark: $BENCHMARK"
  exit 2
fi
