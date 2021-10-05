function scoreAd(adMetadata, bid, auctionConfig, trustedScoringSignals, browserSignals) {
    return bid;
}

function reportResult(auctionConfig, browserSignals) {
  return {
      success: true,
      signalsForWinner: {
          signalForWiner: 1
      },
      reportUrl: 'http://localhost:8084/'
  };
}