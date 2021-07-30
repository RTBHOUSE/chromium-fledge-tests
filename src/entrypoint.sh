#!/bin/bash

# needed because we are changing Chrome's HOME directory
export XAUTHORITY=$HOME/.Xauthority

# using real x server as chromium headless mode is buggy
if [ -v DISPLAY ] && [ -v XAUTH ]; then
  xauth add ${XAUTH#*/}  # with hostname info dropped
else
  vncserver -passwd ~/.vnc/passwd -localhost no -noxstartup :20 &> /dev/null &
  export DISPLAY=:20
fi

exec "$@"
