FROM ubuntu:18.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-setuptools \
    python3.5 \
    python3-pip \
    apache2-utils\
    && \
apt-get clean && \
rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir pandas Click click-config-file matplotlib requests
ENV LC_ALL C.UTF-8
ENV export LANG=C.UTF-8

CMD ["python3", "/home/torchserve_benchmark/benchmark-ab.py", "--config", "/home/torchserve_benchmark/config.json" ]