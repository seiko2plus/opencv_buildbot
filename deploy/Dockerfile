FROM debian:stretch

RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN apt-get update \
 && apt-get install -y sudo apt-utils apt-transport-https build-essential cmake git pkg-config curl \
 && apt-get clean

RUN apt-get update \
 && apt-get install -y libssl-dev libffi-dev python3 python3-dev python3-pip supervisor \
 && apt-get clean

ARG NODE_VERSION=v8.11.1

RUN cd /usr/local/src \
 && curl https://nodejs.org/dist/${NODE_VERSION}/node-${NODE_VERSION}-linux-$(uname -m).tar.xz | tar xJv \
 && mv node-${NODE_VERSION}-linux-$(uname -m) /usr/nodejs \
 && ln -s /usr/nodejs/bin/npm /usr/bin/npm \
 && ln -s /usr/nodejs/bin/node /usr/bin/node \
 && ln -s /usr/nodejs/bin/node /usr/bin/nodejs

RUN pip3 install --upgrade pip
RUN pip3 install virtualenv \
 && npm install --global yarn

CMD ["/app/deploy/entry.sh"]