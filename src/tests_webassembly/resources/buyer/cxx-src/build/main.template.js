
function fillWithRandomFloat32Array(n, vector) {
  for (let i = 0; i < n; i++) {
    vector[i] = (Math.random() * 2) - 1;
  }
  return vector;
}

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

(() => {
  const someFloats = new Array(200);
  fillWithRandomFloat32Array(someFloats.length, someFloats);
  const interestGroup = {
    ads: [{
      renderUrl: 'https://0.0.0.0/renderUrl123',
      metadata: {
        input: someFloats
      }
    }]
  };

  const t_begin = performance.now();

  const bid = generateBid(interestGroup, null, null, null, null).bid;

  const t_end = performance.now();

  console.log("bid: " + bid);
  console.log("time spent on parsing: " + (t_parse_end - t_parse_start) + "ms");
  console.log("time spent on generateBid: " + (t_end - t_begin) + "ms");
  console.log("[sum] time spent on script: " + (t_end - t_parse_start) + "ms");
})();