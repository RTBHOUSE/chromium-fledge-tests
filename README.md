# Chromium-FLEDGE-tests

This repository contains a framework to test [FLEDGE
](https://github.com/WICG/turtledove/blob/main/FLEDGE.md)
implementation capabilities in [Chromium](https://chromium-review.googlesource.com) and is part of research related to expected removal of third-party cookies.

## Run tests  

### Run tests with the latest chromium build

- `bash run.sh`

### Run tests with custom chromium build

- `bash run.sh --chromium-directory <path-to-chromium-dir>`
- `bash run.sh --chromium-url <url-to-chromium-zip>`

## Extra dependencies
* docker