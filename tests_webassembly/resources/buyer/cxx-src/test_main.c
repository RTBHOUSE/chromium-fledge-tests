#include <stdio.h>
#include <stdlib.h>
#include "functions.h"


float rand_float() {
  return ((float)rand()) / ((float)RAND_MAX);
}

void fill_random(size_t size, float v[size]) {
  for (size_t i = 0; i < size; ++i) {
    v[i] = rand_float();
  }
}

void print_2d(size_t rows, size_t cols, const float a[rows][cols]) {
#ifndef NDEBUG
  printf("[ ");
  for (size_t i = 0; i < rows; ++i) {
    printf("[ ");
    for (size_t j = 0; j < cols - 1; ++j) {
      printf("%g, ", a[i][j]);
    }
    if (cols > 0) {
      printf("%g", a[i][cols - 1]);
    }
    printf(" ]");

    if (i < rows - 1) {
      puts(",");
    }

  }
  printf(" ]\n");
#endif
}

void print_1d(size_t size, const float v[size]) {
#ifndef NDEBUG
  printf("[ ");
  for (size_t i = 0; i < size - 1; ++i) {
    printf("%g, ", v[i]);
  }
  if (size > 0) {
    printf("%g", v[size - 1]);
  }
  printf(" ]\n");
#endif
}

int main() {
  srand(12345);

  float m[2][3] = {{1, 2, 3}, {1, 6, 9}};
  float v[3] = {2, 5, 7};
  float result[3];

  printf("m = ");
  print_2d(2, 3, m);
  printf("v = ");
  print_1d(3, v);

  float input[200];
  fill_random(200, input);

  printf("result = ");
  print_1d(200, input);

  printf("%g\n", test_nn_forward(200, input));

  return 0;
}
