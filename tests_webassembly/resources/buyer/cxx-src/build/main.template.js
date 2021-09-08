let wasm_module = undefined;
const t_mid = performance.now();
let time_instantiate = -1;
let time_parse = -1;

function fillWithRandomFloat32Array(n, vector) {
    for (let i = 0; i < n; i++) {
        vector[i] = (Math.random() * 2) - 1;
    }
    return vector;
}

function run_bidding_fn_test() {
    const memory = wasm_module.instance.exports.memory;
    const some_floats = new Float32Array(memory.buffer, 0, 200);
    fillWithRandomFloat32Array(some_floats.length, some_floats);
    return wasm_module.instance.exports.test_nn_forward(some_floats.length, some_floats);
}

WebAssembly.instantiate(wasm_code).then(obj => {
    wasm_module = obj;
}).finally(() => {
    const t_end = performance.now();
    time_parse = t_mid - t_start;
    time_instantiate = t_end - t_mid;
    console.log("parse wasm_code uint8array", time_parse);
    console.log("instantiate", time_instantiate);
}).then(() => {

    const timings = [];
    let first_execution_end = -1;
    for (let i = 0; i < 1000; ++i) {
        const t0 = performance.now();
        run_bidding_fn_test();
        timings.push(performance.now() - t0);
        if (i === 0) {
            first_execution_end = performance.now();
        }
    }
    const total = performance.now() - t_start;
    const results = {
        max: timings.reduce((a, b) => Math.max(a, b)),
        min: timings.reduce((a, b) => Math.min(a, b)),
        avg: timings.reduce((a, b) => a + b) / timings.length,
        loops: timings.length,
        total: total,
        instantiate: time_instantiate,
        parse_wasm: time_parse,
        until_first: first_execution_end - t_start
    };
    console.log(results);
});