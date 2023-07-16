FROM python:3.8-slim

RUN \
    set -eux; \
    apt-get update; \
    DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends \
    python3-pip \
    build-essential \
    python3-venv \
    ffmpeg \
    git \
    ; \
    rm -rf /var/lib/apt/lists/*
RUN pip install tabulate
RUN pip install httpx
RUN pip install pandas
RUN pip3 install -U pip && pip3 install -U wheel && pip3 install -U setuptools==59.5.0
COPY ./requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt && rm -r /tmp/requirements.txt
# Copy the image file into the Docker image
COPY eoa.jpg /code/eoa.jpg
COPY flyer.pdf /code/flyer.pdf

COPY . /code
WORKDIR /code

CMD ["bash"]

