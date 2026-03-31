FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

ENV ARIA_NAME=wz2c
ENV QBIT_NAME=wznox
ENV FFMPEG_NAME=wzeg
ENV FFPROBE_NAME=wzpr

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    git \
    ffmpeg \
    aria2 \
    qbittorrent-nox \
    p7zip-full \
    unzip \
    wget \
    build-essential \
    libmagic-dev \
    default-jre \
    rclone \
    && rm -rf /var/lib/apt/lists/*

RUN mv /usr/bin/qbittorrent-nox /usr/bin/wznox && \
    mv /usr/bin/aria2c /usr/bin/wz2c && \
    mv /usr/bin/ffmpeg /usr/bin/wzeg && \
    mv /usr/bin/ffprobe /usr/bin/wzpr

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app

COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip setuptools && \
    pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["bash", "start.sh"]
