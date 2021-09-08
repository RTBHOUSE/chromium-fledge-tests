#include <stddef.h>
//#include <emscripten/emscripten.h>

#include "functions.h"
#include "model_weights.h"

//void print_2d(size_t rows, size_t cols, const float a[rows][cols]);
//void print_1d(size_t size, const float v[size]);

EMSCRIPTEN_KEEPALIVE void multiply(size_t rows, size_t cols, const float a[rows][cols], const float v[cols], float result[rows]) {
  for (size_t i = 0; i < rows; ++i) {
    result[i] = 0;
    for (size_t j = 0; j < cols; ++j) {
      result[i] += a[i][j] * v[j];
    }
  }
}

inline float max2(float a, float b) {
  return a >= b ? a : b;
}

EMSCRIPTEN_KEEPALIVE void relu(size_t size, float *v) {
  for (size_t i = 0; i < size; ++i) {
    v[i] = max(0.0f, v[i]);
  }
}

EMSCRIPTEN_KEEPALIVE float get(float *v, size_t pos) {
  return v[pos];
}

EMSCRIPTEN_KEEPALIVE float sum(size_t size, float *v) {
  float s = 0;
  while (size) {
    s += v[--size];
  }
  return s;
}

EMSCRIPTEN_KEEPALIVE float test_nn_forward(size_t size, const float input[size]) {

#define nn_step(rows, cols, weights_matrix, vector, result_vector) \
  multiply(rows, cols, weights_matrix, vector, result_vector); \
  relu(cols, result_vector);

  float x1[size], x2[size];

  nn_step(nn_model_weights_0_rows, nn_model_weights_0_cols, nn_model_weights_0, input, x1);
  nn_step(nn_model_weights_1_rows, nn_model_weights_1_cols, nn_model_weights_1, x1, x2);
  nn_step(nn_model_weights_2_rows, nn_model_weights_2_cols, nn_model_weights_2, x2, x1);
  nn_step(nn_model_weights_3_rows, nn_model_weights_3_cols, nn_model_weights_3, x1, x2);

  return x2[0];
}
