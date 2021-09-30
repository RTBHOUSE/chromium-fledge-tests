const tf = require('@tensorflow/tfjs-node');

const fs = require('fs');
const child_process = require('child_process');

eval(fs.readFileSync(__dirname + '/../../../tests_performance/resources/buyer/buyer.js', { encoding: 'UTF-8' }));

Promise.all([nn_model_weights_0, nn_model_weights_1, nn_model_weights_2, nn_model_weights_3, nn_model_weights_4].map((layer_weights, idx) => {
  let model = tf.sequential({
    layers: [
      tf.layers.dense({ inputShape: [200], units: 200, activation: 'relu', useBias: false, weights: [tf.tensor(layer_weights[0]).transpose()] }),
      tf.layers.dense({ units: 100, activation: 'relu', useBias: false, weights: [tf.tensor(layer_weights[1]).transpose()] }),
      tf.layers.dense({ units: 50, activation: 'relu', useBias: false, weights: [tf.tensor(layer_weights[2]).transpose()] }),
      tf.layers.dense({ units: 1, activation: 'relu', useBias: false, weights: [tf.tensor(layer_weights[3]).transpose()] })
    ]
  });
  const modelDir = __dirname + "/model" + idx + "/";
  model.save("file://" + __dirname + "/model" + idx + ".layers/").then(() => {
    child_process.execSync('tensorflowjs_converter --input_format tfjs_layers_model --output_format tfjs_graph_model ' + __dirname + "/model" + idx + ".layers/model.json " + modelDir);
    return tf.loadGraphModel("file://" + modelDir + "model.json", {});
  }).then(model => model.save({
    save: artifacts => {
      fs.writeFileSync(modelDir + "modelTopology.json", JSON.stringify(artifacts.modelTopology));
      fs.writeFileSync(modelDir + "weightSpecs.json", JSON.stringify(artifacts.weightSpecs));
      const weightDataFile = fs.createWriteStream(modelDir + "weightData.js");
      weightDataFile.write('module.exports = Uint8Array.from([');
      Buffer.from(artifacts.weightData).forEach(int => weightDataFile.write(int + ","));
      weightDataFile.end(']).buffer;');
    }
  }));
})).then(all => {
  const browserify = require('browserify');

  const process = require('process');

  browserify(__dirname + '/buyer_template.js')
    .transform('brfs')
    .bundle()
    .pipe(process.stdout);
})
