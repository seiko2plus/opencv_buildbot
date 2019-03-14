FROM alpine:3.7

RUN echo @edgecommunity http://nl.alpinelinux.org/alpine/edge/community >> /etc/apk/repositories \
 && echo @testing http://nl.alpinelinux.org/alpine/edge/testing >> /etc/apk/repositories \
 && apk add --no-cache \
        bash supervisor git python3-dev libffi-dev libressl-dev \
        postgresql-dev py3-pip alpine-sdk tar tzdata xz curl \
        nodejs nodejs-npm yarn

RUN pip3 install --upgrade pip setuptools wheel \
 && pip3 install virtualenv

CMD ["/app/deploy/entry.sh"]
