#ifndef CXX_SRC_FUNCTIONS_H
#define CXX_SRC_FUNCTIONS_H

#include <stddef.h>

#ifndef EMSCRIPTEN_KEEPALIVE
#define EMSCRIPTEN_KEEPALIVE __attribute__((used))
#endif // EMSCRIPTEN_KEEPALIVE

EMSCRIPTEN_KEEPALIVE float nn_forward_model0(size_t size, const float input[size]);
EMSCRIPTEN_KEEPALIVE float nn_forward_model1(size_t size, const float input[size]);
EMSCRIPTEN_KEEPALIVE float nn_forward_model2(size_t size, const float input[size]);
EMSCRIPTEN_KEEPALIVE float nn_forward_model3(size_t size, const float input[size]);
EMSCRIPTEN_KEEPALIVE float nn_forward_model4(size_t size, const float input[size]);

#endif //CXX_SRC_FUNCTIONS_H
