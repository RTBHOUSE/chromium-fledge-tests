function scoreAd(adMetadata, bid, auctionConfig, trustedScoringSignals, browserSignals) {
  return bid;
}

function reportResult(auctionConfig, browserSignals) {
  var signals = {
    "auctionConfig": auctionConfig,
    "browserSignals": browserSignals
  };
  sendReportTo("https://fledge-tests.creativecdn.net:8102/reportResult?signals=" + encodeURIComponent(JSON.stringify(signals)));
}
