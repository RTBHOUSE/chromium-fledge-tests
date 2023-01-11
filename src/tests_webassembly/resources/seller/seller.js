function scoreAd(adMetadata, bid, auctionConfig, trustedScoringSignals, browserSignals) {
  return browserSignals.biddingDurationMsec;
}

function reportResult(auctionConfig, browserSignals) {
  var signals = {
    "auctionConfig": auctionConfig,
    "browserSignals": browserSignals
  };
  sendReportTo("https://localhost:9022/reportResult?signals=" + encodeURIComponent(JSON.stringify(signals)));
}
