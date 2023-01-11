#!/bin/bash

set -xeu

cd "$(dirname "$0")"

openssl genrsa -traditional -out ca.key

openssl req -x509 -key ca.key -out ca.crt -days 3650 -sha256 -subj "/C=PL/ST=Some-State/O=Internet Widgits Pty Ltd/OU=Fledge Tests"

certutil -d nssdb -A -t TC -n "fledge-tests CA" -i ca.crt
