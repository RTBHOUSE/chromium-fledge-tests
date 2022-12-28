#!/bin/bash

# using real x server as chromium headless mode is buggy
if [ -v DISPLAY ] && [ -v XAUTH ]; then
  xauth add ${XAUTH#*/}  # with hostname info dropped
else
  vncserver -passwd ~/.vnc/passwd -xstartup /usr/bin/xterm :20 &> /dev/null &
  export DISPLAY=:20
fi

exec "$@"

