{% extends 'buyer-common.template.js' %}

{% block header %}
var performance;
if (typeof performance === 'undefined') {
    const perfHooks = require('perf_hooks');
    performance = perfHooks.performance;
}

const t_script_begin = performance.now();
{% endblock %}

{% block footer %}

function fillWithRandomFloat32Array(n, vector) {
  for (let i = 0; i < n; i++) {
    vector[i] = (Math.random() * 2) - 1;
  }
  return vector;
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
  console.log("time spent on generateBid: " + (t_end - t_begin) + "ms");
  console.log("[sum] time spent on script: " + (t_end - t_script_begin) + "ms");
})();
{% endblock %}
