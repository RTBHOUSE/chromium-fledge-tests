function multiply(a, b) {
  if (a[0].length !== b.length) {
     throw new Error("invalid matrix dimensions");
  }
  var v = new Array(a.length);
  for (var i = 0; i < a.length; i++) {
    v[i] = 0;
    for (var j = 0; j < b.length; j++) {
      v[i] += a[i][j] * b[j];
    }
  }
  return v;
}

function relu(a) {
    if (a.length > 0) {
        for (let i = 0; i < a.length; ++i) {
            a[i] = Math.max(0, a[i]);
        }
    }
    return a;
}

function nn_forward(input, nn_model_weights) {
    let X = input;
    X = relu(multiply(nn_model_weights[0], X));
    X = relu(multiply(nn_model_weights[1], X));
    X = relu(multiply(nn_model_weights[2], X));
    X = relu(multiply(nn_model_weights[3], X));
    return X[0];
}

function generateBid(interestGroup, auctionSignals, perBuyerSignals, trustedBiddingSignals, browserSignals) {

  const ad = interestGroup.ads[0];
  let input = ad.metadata.input;
  let nn_model_weights = ad.metadata.nn_model_weights;

  let bid = nn_forward(input, nn_model_weights);

  return {'ad': 'example',
          'bid': bid,
          'render': ad.renderUrl};
}

function reportWin(auctionSignals, perBuyerSignals, sellerSignals, browserSignals) {
  const signals = {
    "auctionSignals": auctionSignals,
    "perBuyerSignals": perBuyerSignals,
    "sellerSignals": sellerSignals,
    "browserSignals": browserSignals
  };
  sendReportTo("https://fledge-tests.creativecdn.net:9001/reportWin?signals=" + encodeURIComponent(JSON.stringify(signals)));
}
