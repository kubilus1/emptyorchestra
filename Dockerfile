FROM ubuntu:bionic

RUN apt-get update && apt-get install -y \
    pex pkg-config libglib2.0-dev libgirepository1.0-dev \
    libcairo2-dev python3-cairo-dev libssl-dev libpython3-dev python3-pip
