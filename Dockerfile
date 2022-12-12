FROM ubuntu:20.04

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
        curl ca-certificates software-properties-common unzip libnss3-tools \
        xorg \
        `# we use actual x server as chromium headless mode is buggy` \
        tigervnc-common tigervnc-standalone-server \
        python3 python3-pip \
        `# chromium dependencies` \
        libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
        libxkbcommon0 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 \
        libgbm1 libpango1.0-0 libcairo2 libasound2 libxshmfence1 && \
    rm -rf /var/lib/apt/lists/*; \
    useradd -m -s /bin/bash -u 11031 usertd; \
    mkdir -p /run/systemd && echo 'docker' > /run/systemd/container

USER usertd
WORKDIR /home/usertd

RUN pip3 install --user selenium assertpy influxdb; \
    mkdir /home/usertd/logs

COPY src/common/ssl/ca/ca.crt tests/common/ssl/ca/ca.crt

RUN mkdir -p /home/usertd/.pki/nssdb && \
    certutil -d /home/usertd/.pki/nssdb -N --empty-password && \
    certutil -d sql:/home/usertd/.pki/nssdb/ -A -t TC -n "fledge-tests CA" -i /home/usertd/tests/common/ssl/ca/ca.crt

WORKDIR /home/usertd/tests
VOLUME /home/usertd/logs

# This is a hack due to https://bugs.chromium.org/p/chromium/issues/detail?id=1229652
RUN mkdir -p ~/.vnc && echo turtledove | vncpasswd -f > ~/.vnc/passwd && touch ~/.Xauthority

COPY src/. .

ENTRYPOINT [ "/home/usertd/tests/entrypoint.sh" ]
CMD /home/usertd/tests/run_tests.sh
