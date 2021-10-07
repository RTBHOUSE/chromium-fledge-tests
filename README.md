# Chromium-FLEDGE-tests

This repository contains a framework to test [FLEDGE](https://github.com/WICG/turtledove/blob/main/FLEDGE.md)
implementation capabilities in [Chromium](https://chromium-review.googlesource.com) and is part of research related to anticipated removal of third-party cookies. It supports end-to-end functional and performance FLEDGE testing.

- [How to run tests](#how-to-run-tests)
- [Functional tests](#functional-tests)
- [Performance benchmarks](#performance-benchmarks)
  - [benchmark 1: tight loop with a warm-up run in V8 engine with jit](#benchmark-1-tight-loop-with-a-warm-up-run-in-v8-engine-with-jit)
  - [benchmark 2: buyer’s js run as a bidding worklet in Chromium](#benchmark-2-buyers-js-run-as-a-bidding-worklet-in-chromium)

## How to run tests  

- `bash run.sh` - runs all tests with the latest chromium version
- `bash run.sh --chromium-directory <path-to-chromium-dir>` - runs tests with custom-built chromium from given local path
- `bash run.sh --chromium-url <url-to-chromium-zip>`  - downloads chromium from the given location and runs tests with it

## Functional tests

In the [tests](https://github.com/RTBHOUSE/chromium-fledge-tests/blob/master/tests_functional/test.py) we simulate an end-to-end FLEDGE flow, which includes joining interest groups and running ad auctions. The tests launch the latest or custom-built Chromium browser with Selenium. They serve mock servers which provide buyer's and seller's logic including the `joinAdInterestGroup()` and `runAdAuction()` API calls. These mock servers track all requests, so we could verify not just the rendered ad but also the signals passed to `reportWin()` and `reportResult()`. Here is an example:

```javascript
    def setUp(self) -> None:
        options = webdriver.ChromeOptions()
        ...
        options.add_argument('--enable-features=FledgeInterestGroups,FledgeInterestGroupAPI')
        self.driver = webdriver.Chrome(...)
```

```javascript
    def test__should_show_ad_our(self):
        with MockServer(8091, '/home/usertd/tests/tests_functional/resources/buyer') as buyer_server,\
                MockServer(8092, '/home/usertd/tests/tests_functional/resources/seller') as seller_server:

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
            .is_equal_to("https://fledge-tests.creativecdn.net:8091")
        assert_that(report_result_signals.get('browserSignals').get('renderUrl')) \
            .is_equal_to("https://fledge-tests.creativecdn.net:8091/ad-1.html")

        report_win_signals = buyer_server.get_first_request("/reportWin").get_first_json_param('signals')
        logger.info(f"reportWin() signals: {pretty_json(report_win_signals)}")
        assert_that(report_win_signals.get('browserSignals').get('interestGroupOwner')) \
            .is_equal_to("https://fledge-tests.creativecdn.net:8091")
        assert_that(report_win_signals.get('browserSignals').get('renderUrl')) \
            .is_equal_to("https://fledge-tests.creativecdn.net:8091/ad-1.html")
```

## Performance benchmarks

We test the same `generateBid()` in two different environments:

```javascript
function generateBid(input, nn_models_weights) {
  return nn_forward(input, nn_models_weights[0]) * nn_forward(input, nn_models_weights[1])
            * nn_forward(input, nn_models_weights[2]) * nn_forward(input, nn_models_weights[3])
            * nn_forward(input, nn_models_weights[4]);
}
```

Some motivation and implementation details were presented in this [issue](https://github.com/WICG/turtledove/issues/215).

### benchmark 1: tight loop with a warm-up run in V8 engine with jit

In this scenario we run [V8 engine](https://github.com/andreburgaud/docker-v8) with [js script](https://github.com/RTBHOUSE/chromium-fledge-tests/blob/master/tests_performance/resources/benchmark.js), which calls `generateBid()` inside a loop including some warm-up phase. Inputs and weights are different for every iteration and generated before the test. Results are output to avoid unwanted optimizations.

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

In this scenario we use this testing framework to run [buyer's js script](https://raw.githubusercontent.com/RTBHOUSE/chromium-fledge-tests/master/tests_performance/resources/buyer/buyer.js) in a bidding worklet (with these limitations: jitless, v8 pool size set to 1 etc.). In this instance, `generateBid()` is called once with hard-coded weights. In this [test](https://github.com/RTBHOUSE/chromium-fledge-tests/blob/master/tests_performance/test.py) we use a custom-built version of chromium with a [patch](https://github.com/RTBHOUSE/chromium/commits/auction_timer), which helps to measure the bidding worklet time. The following example is similar to previous [functional test](#functional-tests):

```javascript
    def test__check_nn_with_static_weights_computation_time(self):
        with MockServer(9011, '/home/usertd/tests/tests_performance/resources/buyer') as buyer_server,\
                MockServer(9012, '/home/usertd/tests/tests_performance/resources/seller') as seller_server:

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
$ bash run.sh --chromium-url https://github.com/RTBHOUSE/chromium/releases/download/94.0.4588.0-auction-timer/chromium.zip
...
INFO:/home/usertd/tests/tests_performance/test.py:generateBid took: 55.68 ms
```

### benchmark 3: buyer's js using TensorFlowJS models run as a bidding worklet in Chromium

This is a similar scenario but it uses a pre-built TensorflowJS model in [buyer's js script](tests_tensorflow/resources/buyer/buyer.js). It also requires a custom-built version of chromium with a [patch](https://github.com/RTBHOUSE/chromium/commits/async_5000ms), which extends bidding worklets timeout to 5s:

Result:

```bash
$ bash build.sh
$ bash run.sh --test tests_tensorflow.test --chromium-url https://github.com/RTBHOUSE/chromium/releases/download/96.0.4644.0-async-5000ms/chromium-async_5000ms.zip
...
INFO:/home/usertd/tests/tests_tensorflow/test.py:generateBid took: 370 ms
```
