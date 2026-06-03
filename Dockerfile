FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    iproute2 \
    tcpdump \
    iputils-ping \
    net-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pandas matplotlib

WORKDIR /app

COPY . /app/

RUN chmod +x /app/scripts/setup_tc.sh

EXPOSE 5000

