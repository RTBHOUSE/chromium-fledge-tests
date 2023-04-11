# Chromium-FLEDGE-tests

This repository contains a framework to test [FLEDGE](https://github.com/WICG/turtledove/blob/main/FLEDGE.md)
implementation capabilities in [Chromium](https://chromium-review.googlesource.com) and is part of research related to anticipated removal of third-party cookies. It supports end-to-end functional and performance FLEDGE testing.

- [How to run tests](#how-to-run-tests)
- [Functional tests](#functional-tests)
- [Performance benchmarks](#performance-benchmarks)
  - [benchmark 1: tight loop with a warm-up run in V8 engine with jit](#benchmark-1-tight-loop-with-a-warm-up-run-in-v8-engine-with-jit)
  - [benchmark 2: buyer’s js run as a bidding worklet in Chromium](#benchmark-2-buyers-js-run-as-a-bidding-worklet-in-chromium)
  - [benchmark 3: buyer’s js without wasm run in V8 engine](#benchmark-3-buyers-js-without-wasm-run-in-V8-engine)
  - [benchmark 4: buyer’s js with wasm run in V8 engine](#benchmark-4-buyers-js-with-wasm-run-in-V8-engine)
  - [benchmark 5: buyer’s js with wasm run as a bidding worklet in Chromium](#benchmark-5-buyers-js-with-wasm-run-as-a-bidding-worklet-in-chromium)

## How to run tests  

- `bash run.sh [--chromium-revision latest]` - runs all tests with the latest chromium version
- `bash run.sh --downloaded` - runs all tests with previously downloaded browser version
- `bash run.sh --test <module>` - runs all tests from given module (e.g. tests_functional.test)
- `bash run.sh --test-dir <path-to-python-test>` - runs all tests from given local path
- `bash run.sh --chromium-revision <chromium-snaphot-revision>` - runs tests with specified chromium revision
- `bash run.sh --chromium-dir <path-to-chromium-dir>` - runs tests with from given local path containing Chrome/Chromium with proper chromedriver
- `bash run.sh --chromium-url <url-to-chromium-zip>`  - downloads custom-built chromium with chromedriver from the given location and runs tests with it
- `bash run.sh --chromium-url <url-to-chrome-deb> [--chromedriver-url <url-to-chromedriver-zip>]`  - downloads official Chrome release from specified location and runs tests with it. Proper chromedriver is automatically detected and downloaded, but may be overridden.

### Example (Chrome Stable)
```
bash ./run.sh \
    --chromium-url \
    https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
```

### Example (Chrome Beta)
```
bash ./run.sh \
    --chromium-url \
    https://dl.google.com/linux/direct/google-chrome-beta_current_amd64.deb
```

### Example (Chrome Dev)
```
bash ./run.sh \
    --chromium-url \
    https://dl.google.com/linux/direct/google-chrome-unstable_current_amd64.deb
```


## Functional tests

In the [tests](https://github.com/RTBHOUSE/chromium-fledge-tests/blob/master/src/tests_functional/test.py) we simulate an end-to-end FLEDGE flow, which includes joining interest groups and running ad auctions. The tests launch the latest or custom-built Chromium browser with Selenium. They serve mock servers which provide buyer's and seller's logic including the `joinAdInterestGroup()` and `runAdAuction()` API calls. These mock servers track all requests, so we could verify not just the rendered ad but also the signals passed to `reportWin()` and `reportResult()`. Here is an example:

```python
    def setUp(self) -> None:
        options = webdriver.ChromeOptions()
        ...
        options.add_argument('--enable-features=FledgeInterestGroups,FledgeInterestGroupAPI')
        self.driver = webdriver.Chrome(...)
```

```python
    def test__should_show_ad_our(self):
        with MockServer(port=8091, directory='resources/buyer') as buyer_server,\
                MockServer(port=8092, directory='resources/seller') as seller_server:

            with MeasureDuration("joinAdInterestGroup"):
                self.driver.get(buyer_server.address)
                self.assertDriverContainsText('body', 'joined interest group')

            with MeasureDuration("runAdAuction"):
                self.driver.get(seller_server.address)
                WebDriverWait(self.driver, 5)\
                    .until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe')))
                self.assertDriverContainsText('body', 'TC AD 1')

        report_result_signals = seller_server.get_first_request("/reportResult").get_first_json_param('signals')
        logger.info(f"reportResult() signals: {pretty_json(report_result_signals)}")
        assert_that(report_result_signals.get('browserSignals').get('interestGroupOwner'))\
            .is_equal_to("https://localhost:8091")
        assert_that(report_result_signals.get('browserSignals').get('renderUrl')) \
            .is_equal_to("https://localhost:8091/ad-1.html")

        report_win_signals = buyer_server.get_first_request("/reportWin").get_first_json_param('signals')
        logger.info(f"reportWin() signals: {pretty_json(report_win_signals)}")
        assert_that(report_win_signals.get('browserSignals').get('interestGroupOwner')) \
            .is_equal_to("https://localhost:8091")
        assert_that(report_win_signals.get('browserSignals').get('renderUrl')) \
            .is_equal_to("https://localhost:8091/ad-1.html")
```

## Performance benchmarks

We test the same `generateBid()` in different environments:

```javascript
function generateBid(input, nn_models_weights) {
  return nn_forward(input, nn_models_weights[0]) * nn_forward(input, nn_models_weights[1])
            * nn_forward(input, nn_models_weights[2]) * nn_forward(input, nn_models_weights[3])
            * nn_forward(input, nn_models_weights[4]);
}
```

Some motivation and implementation details were presented in this [issue](https://github.com/WICG/turtledove/issues/215).

### benchmark 1: tight loop with a warm-up run in V8 engine with jit

In this scenario we run [V8 engine](https://github.com/andreburgaud/docker-v8) with [js script](https://github.com/RTBHOUSE/chromium-fledge-tests/blob/master/src/tests_performance/resources/benchmark.js), which calls `generateBid()` inside a loop including some warm-up phase. Inputs and weights are different for every iteration and generated before the test. Results are output to avoid unwanted optimizations.

```javascript
function test(warmups, loops) {
    if (warmups > loops) {
        throw new Error("warmups greater than loops");
    }
    let bids = new Array(loops);
    let inputs = new Array(loops);
    let nn_models_weights = new Array(loops);

    for (let i = 0; i < loops; i++) {
        inputs[i] = randomVector(200);
        nn_models_weights[i] = new Array(5);
        for (let model = 0; model < 5; model++) {
            nn_models_weights[i][model] = new Array(4);
            nn_models_weights[i][model][0] = randomMatrix(200, 200);
            nn_models_weights[i][model][1] = randomMatrix(100, 200);
            nn_models_weights[i][model][2] = randomMatrix(50, 100);
            nn_models_weights[i][model][3] = randomMatrix(1, 50);
        }
    }
    let start = 0;
    for (let i = 0; i < loops; i++) {
        if (i == warmups) {
            start = new Date().getTime();
        }
        bids[i] = generateBid(inputs[i], nn_models_weights[i]);
    }
    let end = new Date().getTime();
    let avgDuration = ((end - start) / (loops - warmups));
    avgDuration = Math.round(avgDuration * 100) / 100;

    console.log("results for", loops, "iterations: ", bids);
    console.log("time spent on 1 loop in avg:", avgDuration, "ms");
}
```
Result:

```bash
$ docker run --rm -it -v $PWD/src/tests_performance:/tests_performance/ andreburgaud/d8 /tests_performance/resources/benchmark.js
...
time spent on 1 loop in avg: 1.12 ms
```

### benchmark 2: buyer's js run as a bidding worklet in Chromium

In this scenario we use this testing framework to run [buyer's js script](https://raw.githubusercontent.com/RTBHOUSE/chromium-fledge-tests/master/src/tests_performance/resources/buyer/buyer.js) in a bidding worklet (with these limitations: jitless, v8 pool size set to 1 etc.). In this instance, `generateBid()` is called once with hard-coded weights. In this [test](https://github.com/RTBHOUSE/chromium-fledge-tests/blob/master/src/tests_performance/test.py) we use a custom-built version of chromium with a [patch](https://github.com/RTBHOUSE/chromium/commits/rtb_master), which helps to measure the bidding worklet time. The following example is similar to previous [functional test](#functional-tests):

```python
    def test__check_nn_with_static_weights_computation_time(self):
        with MockServer(port=9011, directory='resources/buyer') as buyer_server,\
                MockServer(port=9012, directory='resources/seller') as seller_server:

            with MeasureDuration("joinAdInterestGroup"):
                self.driver.get(buyer_server.address)
                self.assertDriverContainsText('body', 'joined interest group')

            with MeasureDuration("runAdAuction"):
                self.driver.get(seller_server.address)
                WebDriverWait(self.driver, 5)\
                    .until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe')))
                self.assertDriverContainsText('body', 'TC AD')

        report_result_signals = seller_server.get_first_request("/reportResult").get_first_json_param('signals')
        logger.info(f"reportResult() signals: {pretty_json(report_result_signals)}")

        report_win_signals = buyer_server.get_first_request("/reportWin").get_first_json_param('signals')
        logger.info(f"reportWin() signals: {pretty_json(report_win_signals)}")

        # to be able to measure bidding worklet time you should use custom-built version of chromium
        # with a patch like this: https://github.com/RTBHOUSE/chromium/commits/auction_timer
        if 'bid_duration' in report_result_signals.get('browserSignals'):
            bid_duration_ms = int(report_result_signals.get('browserSignals').get('bid_duration')) / 1000
            logger.info(f"generateBid took: {bid_duration_ms} ms")
```

Result:

```bash
$ bash run.sh --test tests_performance.test --chromium-url https://github.com/RTBHOUSE/chromium/releases/download/97.0.4674.0-rtb-master/chromium-97.0.4674.0-rtb-master.zip
...
INFO:/home/usertd/tests/tests_performance/test.py:generateBid took: 55.68 ms
```

EDIT: In this benchmark we used Chromium with default flags which add debug asserts and have some overhead, mainly in the case of [benchmark 5](#benchmark-5-buyers-js-with-wasm-run-as-a-bidding-worklet-in-chromium) (reference: [this comment](https://github.com/WICG/turtledove/issues/215#issuecomment-963618254)). The same benchmark run with a new Chromium build without debug asserts:

```bash
$ bash run.sh --test tests_performance.test --chromium-url https://github.com/RTBHOUSE/chromium/releases/download/98.0.4697.0-rtb-master-without-asserts/chromium-98.0.4697.0-rtb-master-without-asserts.zip
...
INFO:/home/usertd/tests/common/utils/__init__.py:[rtb-chromium-debug] AuctionV8Helper::Compile() https://localhost:9011/buyer.js duration: 86.875 ms
INFO:/home/usertd/tests/common/utils/__init__.py:[rtb-chromium-debug] AuctionV8Helper::RunScript() generateBid run() duration: 3.448 ms
INFO:/home/usertd/tests/common/utils/__init__.py:[rtb-chromium-debug] AuctionV8Helper::RunScript() generateBid get() duration: 0.002 ms
INFO:/home/usertd/tests/common/utils/__init__.py:[rtb-chromium-debug] AuctionV8Helper::RunScript() generateBid call() duration: 50.11 ms
...
INFO:/home/usertd/tests/tests_performance/test.py:generateBid took: 53.56 ms
```

### benchmark 3: buyer’s js without wasm run in V8 engine

In this scenario we run [js script](https://github.com/RTBHOUSE/chromium-fledge-tests/blob/master/src/tests_performance/resources/benchmark.js) in V8 engine. It is the same script which was used in benchmark 1 but we do not use jit this time.

Result:

```bash
$ docker run --rm -it -v $PWD/src/tests_performance:/tests_performance/ andreburgaud/d8 /tests_performance/resources/benchmark.js --jitless --optimize_for_size --no-expose-wasm
...
time spent on 1 loop in avg: 54.56 ms
```
### benchmark 4: buyer’s js with wasm run in V8 engine

In this scenario we run [js script with wasm binary hardcoded](https://github.com/RTBHOUSE/chromium-fledge-tests/blob/master/src/tests_webassembly/resources/buyer/buyer-v8.js). It uses the same `generateBid()` but model weights and matrix multiplication are [implemented in C++](https://github.com/RTBHOUSE/chromium-fledge-tests/blob/master/src/tests_webassembly/resources/buyer/cxx-src/functions.c), compiled and hardcoded as a wasm binary:

```javascript
const wasm_code = Uint8Array.from([0,97,115, ... , ]);

function generateBid(interestGroup, auctionSignals, perBuyerSignals, trustedBiddingSignals, browserSignals) {
  let ad = interestGroup.ads[0];
  let input = ad.metadata.input;

  const module = new WebAssembly.Module(wasm_code);
  const instance = new WebAssembly.Instance(module);

  const memory = instance.exports.memory;
  const input_in_memory = new Float32Array(memory.buffer, 0, 200);
  for (let i = 0; i < input.length; ++i) {
    input_in_memory[i] = input[i];
  }
  const results = [
    instance.exports.nn_forward_model0(input_in_memory.length, input_in_memory),
    instance.exports.nn_forward_model1(input_in_memory.length, input_in_memory),
    instance.exports.nn_forward_model2(input_in_memory.length, input_in_memory),
    instance.exports.nn_forward_model3(input_in_memory.length, input_in_memory),
    instance.exports.nn_forward_model4(input_in_memory.length, input_in_memory),
  ];
  const bid = results.map(x => Math.max(x, 1)).reduce((x, y) => x * y);
  return {
    ad: 'example',
    bid: bid,
    render: ad.renderUrl
  }
  
}
```

Result:

```bash
$ bash src/tests_webassembly/resources/buyer/compile.sh
$ docker run --rm -it -v $PWD/src/tests_webassembly:/tests_webassembly andreburgaud/d8 /tests_webassembly/resources/buyer/buyer-v8.js --optimize_for_size
...
time spent on parsing: 1.1640000000000157ms
time spent on generateBid: 3.6059999999999945ms
[sum] time spent on script: 4.927999999999997ms
```

### benchmark 5: buyer’s js with wasm run as a bidding worklet in Chromium

In this [scenario](https://github.com/RTBHOUSE/chromium-fledge-tests/blob/master/src/tests_webassembly/test.py) we run [js script with wasm binary hardcoded](https://github.com/RTBHOUSE/chromium-fledge-tests/blob/master/src/tests_webassembly/resources/buyer/buyer-chromium.js) in a bidding worklet. We have provided another [patch](https://github.com/RTBHOUSE/chromium/commits/rtb_wasm) which turns on webassembly in Chromium. We do not rely on snapshots and we do not take advantage of warm-up. Eventually support for async is not necessary to instantiate webassembly. However, webassembly itself has certain consequences, i.e. it is not possible to turn off `--no-expose-wasm` option without turning off `--jitless`.

```bash
$ bash src/tests_webassembly/resources/buyer/compile.sh
$ bash run.sh --test tests_webassembly.test --chromium-url https://github.com/RTBHOUSE/chromium/releases/download/98.0.4697.0-rtb-wasm-without-asserts/chromium-98.0.4697.0-rtb-wasm-without-asserts.zip
...
INFO:/home/usertd/tests/common/utils/__init__.py:[rtb-chromium-debug] AuctionV8Helper::Compile() https://localhost:9021/buyer-chromium.js duration: 253.986 ms
INFO:/home/usertd/tests/common/utils/__init__.py:[rtb-chromium-debug] AuctionV8Helper::RunScript() generateBid run() duration: 3.811 ms
INFO:/home/usertd/tests/common/utils/__init__.py:[rtb-chromium-debug] AuctionV8Helper::RunScript() generateBid get() duration: 0.004 ms
INFO:/home/usertd/tests/common/utils/__init__.py:[rtb-chromium-debug] AuctionV8Helper::RunScript() generateBid call() duration: 2.253 ms
...
INFO:/home/usertd/tests/tests_webassembly/test.py:generateBid took: 6.07 ms
```

## Running tests without Docker

You can also run tests just like normal Python 3 unittests assuming all [required Python packages](src/requirements.txt) file are installed.

`chrome` binary is searched for in the following places, in order:
* directory specified in `CHROMIUM_DIR` environment variable, if set
* `_chromium` subdirectory (recently downloaded by `get_chromium.sh` script)
* `PATH`

If you set CHROME_HEADLESS=1 in environment, Chrome will run in headless mode (like in case of Docker).
