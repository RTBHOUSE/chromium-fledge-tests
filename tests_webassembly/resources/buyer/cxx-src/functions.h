#ifndef CXX_SRC_FUNCTIONS_H
#define CXX_SRC_FUNCTIONS_H

#include <stddef.h>

#ifndef EMSCRIPTEN_KEEPALIVE
#define EMSCRIPTEN_KEEPALIVE __attribute__((used))
#endif // EMSCRIPTEN_KEEPALIVE

#define unused __attribute__((unused))
#define padding 0  // 0 - no padding, > 0 - pad arrays-like objects to this number of elements
#define max(a,b) \
   ({ __typeof__ (a) _a = (a); \
       __typeof__ (b) _b = (b); \
     _a > _b ? _a : _b; })

EMSCRIPTEN_KEEPALIVE void multiply(size_t rows, size_t cols, const float a[rows][cols], const float v[cols], float result[rows]);

EMSCRIPTEN_KEEPALIVE void relu(size_t size, float v[size]);

EMSCRIPTEN_KEEPALIVE float test_nn_forward(size_t size, const float input[size]);

#endif //CXX_SRC_FUNCTIONS_H
