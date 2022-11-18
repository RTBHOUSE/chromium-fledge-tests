function scoreAd(adMetadata, bid, auctionConfig, trustedScoringSignals, browserSignals) {
  return bid + 100;
}

function reportResult(auctionConfig, browserSignals) {
  var signals = {
    "auctionConfig": auctionConfig,
    "browserSignals": browserSignals
  };
  sendReportTo(auctionConfig.seller + "/reportResult?signals=" + encodeURIComponent(JSON.stringify(signals)));
}
