#!/bin/bash

# using real x server as chromium headless mode is buggy
if [ -v DISPLAY ] && [ -v XAUTH ]; then
  xauth add ${XAUTH#*/}  # with hostname info dropped
else
  vncserver -passwd ~/.vnc/passwd -noxstartup :20 &> /dev/null &
  export DISPLAY=:20
fi

exec "$@"

