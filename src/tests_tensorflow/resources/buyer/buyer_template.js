const modelsArtifacts = [
  {
    modelTopology: require('./model0/modelTopology.json'),
    weightSpecs: require('./model0/weightSpecs.json'),
    weightData: require('./model0/weightData'),
  },
  {
    modelTopology: require('./model1/modelTopology.json'),
    weightSpecs: require('./model1/weightSpecs.json'),
    weightData: require('./model1/weightData'),
  },
  {
    modelTopology: require('./model2/modelTopology.json'),
    weightSpecs: require('./model2/weightSpecs.json'),
    weightData: require('./model2/weightData'),
  },
  {
    modelTopology: require('./model3/modelTopology.json'),
    weightSpecs: require('./model3/weightSpecs.json'),
    weightData: require('./model3/weightData'),
  },
  {
    modelTopology: require('./model4/modelTopology.json'),
    weightSpecs: require('./model4/weightSpecs.json'),
    weightData: require('./model4/weightData'),
  },
];

const tf = require('@tensorflow/tfjs')

generateBid = function (interestGroup, auctionSignals, perBuyerSignals, trustedBiddingSignals, browserSignals) {
  let ad = interestGroup.ads[0];
  let input = tf.tensor(ad.metadata.input, [1, 200]);

  const result = modelsArtifacts.map(artifacts => {
    const handler = { load: () => artifacts };
    const model = new tf.GraphModel(handler, {})
    model.loadSync(handler.load());
    return model.predict(input).dataSync();
  }).reduce((acc, predictionArr) => acc + predictionArr[0], 1);
  return {
    'ad': 'example',
    'bid': result,
    'render': ad.renderUrl
  };
}

reportWin = function (auctionSignals, perBuyerSignals, sellerSignals, browserSignals) {
  const signals = {
    "auctionSignals": auctionSignals,
    "perBuyerSignals": perBuyerSignals,
    "sellerSignals": sellerSignals,
    "browserSignals": browserSignals
  };
  sendReportTo(browserSignals.interestGroupOwner + "/reportWin?signals=" + encodeURIComponent(JSON.stringify(signals)));
}
