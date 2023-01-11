function scoreAd(adMetadata, bid, auctionConfig, trustedScoringSignals, browserSignals) {
  return bid;
}

function reportResult(auctionConfig, browserSignals) {
  var signals = {
    "auctionConfig": auctionConfig,
    "browserSignals": browserSignals
  };
  sendReportTo("https://localhost:8092/reportResult?signals=" + encodeURIComponent(JSON.stringify(signals)));
  return signals;
}
