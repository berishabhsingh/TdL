FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app

COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip setuptools && \
    pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["bash", "start.sh"]
