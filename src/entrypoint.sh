#!/bin/bash

# starting real x server as chromium headless mode is buggy
vncserver -SecurityTypes VncAuth -passwd ~/.vnc/passwd :0 -- xterm &> /dev/null &
export DISPLAY=:0
exec "$@"

