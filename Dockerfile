FROM ubuntu:22.04

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
        curl ca-certificates software-properties-common unzip \
        python3 python3-pip \
        `# chromium dependencies` \
        libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
        libxkbcommon0 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 \
        libgbm1 libpango1.0-0 libcairo2 libasound2 libxshmfence1 python3-jinja2 && \
    rm -rf /var/lib/apt/lists/*; \
    useradd -m -s /bin/bash -u 11031 usertd; \
    mkdir -p /run/systemd && echo 'docker' > /run/systemd/container

ENV CHROME_HEADLESS=1

USER usertd

# Note: run.sh depends on this WORKDIR path
WORKDIR /home/usertd/tests

COPY src/requirements.txt .
RUN pip3 install --user -r requirements.txt

COPY --chown=usertd:usertd src/. .

CMD /home/usertd/tests/run_tests.sh
