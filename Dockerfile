# syntax=docker/dockerfile:1

FROM torizon/tensorflow-lite-sl1680:stable-rc

RUN apt-get update && \
    apt-get install -y --no-install-recommends -t bookworm-backports \
        libdrm2 libdrm-common \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gstreamer1.0-tools \
        gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good \
        gstreamer1.0-plugins-bad \
        gstreamer1.0-libav \
        synap-models \
        libsynacompositor \
        gstreamer1.0-plugins-syna-videoconvertscale \
        gstreamer1.0-plugins-syna-compositor \
        gstreamer1.0-plugins-syna-synap \
        gstreamer1.0-plugins-syna-ai \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends git python3 python3-venv python3-pip python3-gi gir1.2-gstreamer-1.0 gir1.2-gst-plugins-base-1.0 gir1.2-gudev-1.0 && \
    rm -rf /var/lib/apt/lists/* && \
    git clone https://github.com/synaptics-synap/examples.git examples

COPY demo/utils/ examples/utils/
COPY demo/vision/ examples/vision/
COPY demo/requirements-py312.txt examples/requirements-py312.txt
COPY demo/llama_cpp_python-0.3.16-cp311-cp311-linux_aarch64.whl examples/llama_cpp_python-0.3.16-cp311-cp311-linux_aarch64.whl

RUN python3 -m venv examples/.venv --system-site-packages && \
    examples/.venv/bin/python -m pip install --upgrade pip && \
    examples/.venv/bin/pip install -r examples/requirements-py312.txt

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
