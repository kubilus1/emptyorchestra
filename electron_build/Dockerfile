FROM ubuntu:bionic

RUN apt-get update && apt-get install -y python3 python3-pip
RUN python3 -m pip install -U pip
RUN apt-get update && apt-get install -y \
    libpng16-16 libssh-gcrypt-4 python3-gi \
    python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.0 \
    libyaml-dev libcanberra-gtk3-0 libgl1-mesa-dri curl
RUN curl -sL https://deb.nodesource.com/setup_12.x  | bash
RUN apt-get -y install nodejs
RUN npm install electron-builder -g
