function multiplyMatrix(a, b) {
  const rows_a = a.length
  const cols_a = a[0].length;
  const rows_b = b.length;
  const cols_b = b[0].length;

  if (cols_a !== rows_b) {
    throw new Error("Invalid matrix dimensions");
  }

  const c = new Array(rows_a);

  for (let i = 0; i < rows_a; ++i) {
    const row = new Array(cols_b);
    for (let j = 0; j < cols_b; ++j) {
      let s = a[i][0] * b[0][j];
      for (let k = 1; k < cols_a; ++k) {
        s += a[i][k] * b[k][j];
      }
      row[j] = s;
    }
    c[i] = row;
  }

  return c;
}

function relu(a) {
  if (a.length > 0) {
    if (a[0].length > 0) {
      for (let i = 0; i < a.length; ++i) {
        relu(a[i]);
      }
    } else {
      for (let i = 0; i < a.length; ++i) {
        a[i] = Math.max(0, a[i]);
      }
    }
  }

  return a;
}

function test(X, A, B, C, D) {
  let Y = relu(multiplyMatrix(A, X));
  Y = relu(multiplyMatrix(B, Y));
  Y = relu(multiplyMatrix(C, Y));
  Y = relu(multiplyMatrix(D, Y));
  return Y;
}

function generateBid(interestGroup, auctionSignals, perBuyerSignals, trustedBiddingSignals, browserSignals) {

  const ad = interestGroup.ads[0];
  let X = ad.metadata.X;
  let A = ad.metadata.A;
  let B = ad.metadata.B;
  let C = ad.metadata.C;
  let D = ad.metadata.D;

  test(X, A, B, C, D);

  return {'ad': 'example',
          'bid': ad.metadata.bid,
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
