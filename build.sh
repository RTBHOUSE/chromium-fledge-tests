#!/bin/bash

docker build . -f Dockerfile.node --iidfile .iidfile.node

docker run --rm `cat .iidfile.node` node tests_tensorflow/resources/buyer/build_buyer.js > tests_tensorflow/resources/buyer/buyer.js
