#!/bin/bash

set -xeu

cd "$(dirname "$0")"

openssl genrsa -traditional -out localhost.key

openssl req -x509 -config conf.conf -new -key localhost.key \
    -CA ca/ca.crt -CAkey ca/ca.key -CAcreateserial \
    -out localhost.crt -days 3650 -sha256 \
    -extensions v3_req
