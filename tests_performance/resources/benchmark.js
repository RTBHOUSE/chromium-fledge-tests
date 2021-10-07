function randomValue() {
    var u = 0, v = 0;
    while(u === 0) u = Math.random();
    while(v === 0) v = Math.random();
    return Math.sqrt( -2.0 * Math.log( u ) ) * Math.cos( 2.0 * Math.PI * v );
}

function randomVector(n) {
    const vector = new Array(n);
    for (let i = 0; i < n; i++) {
        vector[i] = randomValue();
    }
    return vector;
}

function randomMatrix(n, m) {
    const matrix = new Array(n);
    for (let i = 0; i < n; i++) {
        matrix[i] = randomVector(m);
    }
    return matrix;
}

function multiply(a, b) {
  if (a[0].length !== b.length) {
     throw new Error("invalid matrix dimensions");
  }
  var v = new Array(a.length);
  for (var i = 0; i < a.length; i++) {
    v[i] = 0;
    for (var j = 0; j < b.length; j++) {
      v[i] += a[i][j] * b[j];
    }
  }
  return v;
}

function relu(a) {
    if (a.length > 0) {
        for (let i = 0; i < a.length; ++i) {
            a[i] = Math.max(0, a[i]);
        }
    }
    return a;
}

function nn_forward(input, nn_model_weights) {
    let X = input;
    X = relu(multiply(nn_model_weights[0], X));
    X = relu(multiply(nn_model_weights[1], X));
    X = relu(multiply(nn_model_weights[2], X));
    X = relu(multiply(nn_model_weights[3], X));
    return X[0];
}

function generateBid(input, nn_models_weights) {
  return nn_forward(input, nn_models_weights[0]) * nn_forward(input, nn_models_weights[1])
            * nn_forward(input, nn_models_weights[2]) * nn_forward(input, nn_models_weights[3])
            * nn_forward(input, nn_models_weights[4]);
}

function test(warmups, loops) {
    if (warmups > loops) {
        throw new Error("warmups greater than loops");
    }
    let bids = new Array(loops);
    let inputs = new Array(loops);
    let nn_models_weights = new Array(loops);

    for (let i = 0; i < loops; i++) {
        inputs[i] = randomVector(200);
        nn_models_weights[i] = new Array(5);
        for (let model = 0; model < 5; model++) {
            nn_models_weights[i][model] = new Array(4);
            nn_models_weights[i][model][0] = randomMatrix(200, 200);
            nn_models_weights[i][model][1] = randomMatrix(100, 200);
            nn_models_weights[i][model][2] = randomMatrix(50, 100);
            nn_models_weights[i][model][3] = randomMatrix(1, 50);
        }
    }
    let start = 0;
    for (let i = 0; i < loops; i++) {
        if (i == warmups) {
            start = new Date().getTime();
        }
        bids[i] = generateBid(inputs[i], nn_models_weights[i]);
    }
    let end = new Date().getTime();
    let avgDuration = ((end - start) / (loops - warmups));
    avgDuration = Math.round(avgDuration * 100) / 100;

    console.log("results for", loops, "iterations: ", bids);
    console.log("time spent on 1 loop in avg:", avgDuration, "ms");

}

test(10, 100);
