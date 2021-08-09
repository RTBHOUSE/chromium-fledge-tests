function generateBid(interestGroup, auctionSignals, perBuyerSignals, trustedBiddingSignals, browserSignals) {
  const ad = interestGroup.ads[0];
  return {'ad': 'example',
          'bid': 10,
          'render': ad.renderUrl};
}


function reportWin(auctionSignals, perBuyerSignals, sellerSignals, browserSignals) {
  sendReportTo("http://localhost:8084?" + encodeURIComponent(JSON.stringify(browserSignals)));
}
