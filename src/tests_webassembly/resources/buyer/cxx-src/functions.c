#include <stddef.h>

#include "functions.h"
#include "model_weights.h"

EMSCRIPTEN_KEEPALIVE void multiply(size_t rows, size_t cols, const float a[rows][cols], const float v[cols], float result[rows]) {
  for (size_t i = 0; i < rows; ++i) {
    result[i] = 0;
    for (size_t j = 0; j < cols; ++j) {
      result[i] += a[i][j] * v[j];
    }
  }
}

inline float max(float a, float b) {
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

EMSCRIPTEN_KEEPALIVE float nn_forward_model0(size_t size, const float input[size]) {

#define nn_step(rows, cols, weights_matrix, vector, result_vector) \
  multiply(rows, cols, weights_matrix, vector, result_vector); \
  relu(cols, result_vector);

  float x1[size], x2[size];

  nn_step(nn_model_weights_0_0_rows, nn_model_weights_0_0_cols, nn_model_weights_0_0, input, x1);
  nn_step(nn_model_weights_0_1_rows, nn_model_weights_0_1_cols, nn_model_weights_0_1, x1, x2);
  nn_step(nn_model_weights_0_2_rows, nn_model_weights_0_2_cols, nn_model_weights_0_2, x2, x1);
  nn_step(nn_model_weights_0_3_rows, nn_model_weights_0_3_cols, nn_model_weights_0_3, x1, x2);

  return x2[0];
}

EMSCRIPTEN_KEEPALIVE float nn_forward_model1(size_t size, const float input[size]) {

#define nn_step(rows, cols, weights_matrix, vector, result_vector) \
  multiply(rows, cols, weights_matrix, vector, result_vector); \
  relu(cols, result_vector);

  float x1[size], x2[size];

  nn_step(nn_model_weights_1_0_rows, nn_model_weights_1_0_cols, nn_model_weights_1_0, input, x1);
  nn_step(nn_model_weights_1_1_rows, nn_model_weights_1_1_cols, nn_model_weights_1_1, x1, x2);
  nn_step(nn_model_weights_1_2_rows, nn_model_weights_1_2_cols, nn_model_weights_1_2, x2, x1);
  nn_step(nn_model_weights_1_3_rows, nn_model_weights_1_3_cols, nn_model_weights_1_3, x1, x2);

  return x2[0];
}

EMSCRIPTEN_KEEPALIVE float nn_forward_model2(size_t size, const float input[size]) {

#define nn_step(rows, cols, weights_matrix, vector, result_vector) \
  multiply(rows, cols, weights_matrix, vector, result_vector); \
  relu(cols, result_vector);

  float x1[size], x2[size];

  nn_step(nn_model_weights_2_0_rows, nn_model_weights_2_0_cols, nn_model_weights_2_0, input, x1);
  nn_step(nn_model_weights_2_1_rows, nn_model_weights_2_1_cols, nn_model_weights_2_1, x1, x2);
  nn_step(nn_model_weights_2_2_rows, nn_model_weights_2_2_cols, nn_model_weights_2_2, x2, x1);
  nn_step(nn_model_weights_2_3_rows, nn_model_weights_2_3_cols, nn_model_weights_2_3, x1, x2);

  return x2[0];
}

EMSCRIPTEN_KEEPALIVE float nn_forward_model3(size_t size, const float input[size]) {

#define nn_step(rows, cols, weights_matrix, vector, result_vector) \
  multiply(rows, cols, weights_matrix, vector, result_vector); \
  relu(cols, result_vector);

  float x1[size], x2[size];

  nn_step(nn_model_weights_3_0_rows, nn_model_weights_3_0_cols, nn_model_weights_3_0, input, x1);
  nn_step(nn_model_weights_3_1_rows, nn_model_weights_3_1_cols, nn_model_weights_3_1, x1, x2);
  nn_step(nn_model_weights_3_2_rows, nn_model_weights_3_2_cols, nn_model_weights_3_2, x2, x1);
  nn_step(nn_model_weights_3_3_rows, nn_model_weights_3_3_cols, nn_model_weights_3_3, x1, x2);

  return x2[0];
}

EMSCRIPTEN_KEEPALIVE float nn_forward_model4(size_t size, const float input[size]) {

#define nn_step(rows, cols, weights_matrix, vector, result_vector) \
  multiply(rows, cols, weights_matrix, vector, result_vector); \
  relu(cols, result_vector);

  float x1[size], x2[size];

  nn_step(nn_model_weights_4_0_rows, nn_model_weights_4_0_cols, nn_model_weights_4_0, input, x1);
  nn_step(nn_model_weights_4_1_rows, nn_model_weights_4_1_cols, nn_model_weights_4_1, x1, x2);
  nn_step(nn_model_weights_4_2_rows, nn_model_weights_4_2_cols, nn_model_weights_4_2, x2, x1);
  nn_step(nn_model_weights_4_3_rows, nn_model_weights_4_3_cols, nn_model_weights_4_3, x1, x2);

  return x2[0];
}

