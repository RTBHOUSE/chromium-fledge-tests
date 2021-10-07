function generateBid(interestGroup, auctionSignals, perBuyerSignals, trustedBiddingSignals, browserSignals) {
  const ad = interestGroup.ads[0];
  return {'ad': 'example',
          'bid': trustedBiddingSignals.key1,
          'render': ad.renderUrl};
}

function reportWin(auctionSignals, perBuyerSignals, sellerSignals, browserSignals) {
  var signals = {
    "auctionSignals": auctionSignals,
    "perBuyerSignals": perBuyerSignals,
    "sellerSignals": sellerSignals,
    "browserSignals": browserSignals
  };
  sendReportTo("https://fledge-tests.creativecdn.net:8101/reportWin?signals=" + encodeURIComponent(JSON.stringify(signals)));
}
