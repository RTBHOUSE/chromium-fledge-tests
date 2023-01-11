function generateBid(interestGroup, auctionSignals, perBuyerSignals, trustedBiddingSignals, browserSignals) {
  const ad = interestGroup.ads[0];
  return {'ad': 'example',
          'bid': ad.metadata.bid,
          'render': ad.renderUrl};
}

function reportWin(auctionSignals, perBuyerSignals, sellerSignals, browserSignals) {
  var signals = {
    "auctionSignals": auctionSignals,
    "perBuyerSignals": perBuyerSignals,
    "sellerSignals": sellerSignals,
    "browserSignals": browserSignals
  };
  sendReportTo("https://localhost:8091/reportWin?signals=" + encodeURIComponent(JSON.stringify(signals)));
}
