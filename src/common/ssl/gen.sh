#!/bin/bash

openssl req -config conf.conf -new -key fledge-tests.creativecdn.net.key -out fledge-tests.creativecdn.net.csr

openssl x509 -req -in fledge-tests.creativecdn.net.csr \
    -CA ca/ca.pem -CAkey ca/ca.key -CAcreateserial \
    -out fledge-tests.creativecdn.net.crt -days 3650 -sha256 \
    -extensions v3_req -extfile conf.conf

rm fledge-tests.creativecdn.net.csr
