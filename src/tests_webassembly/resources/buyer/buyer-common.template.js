"use strict";

{% block header %}
{% endblock %}

const wasm_code = Uint8Array.from({{ wasm_code }});
const module = new WebAssembly.Module(wasm_code);
const instance = new WebAssembly.Instance(module);

function generateBid(interestGroup, auctionSignals, perBuyerSignals, trustedBiddingSignals, browserSignals) {
  let ad = interestGroup.ads[0];
  let input = ad.metadata.input;

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

function reportWin(auctionSignals, perBuyerSignals, sellerSignals, browserSignals) {
  const signals = {
    "auctionSignals": auctionSignals,
    "perBuyerSignals": perBuyerSignals,
    "sellerSignals": sellerSignals,
    "browserSignals": browserSignals
  };
  sendReportTo("https://localhost:9021/reportWin?signals=" + encodeURIComponent(JSON.stringify(signals)));
}

{% block footer %}
{% endblock %}
