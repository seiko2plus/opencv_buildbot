#!/bin/bash

if [ -f /app/deploy/env.sh ]; then
  . /app/deploy/env.sh
fi

umask 0000
virtualenv --system-site-packages /env
. /env/bin/activate

set -x

(
    cd /app/deploy
    pip3 install -r pyrequirements.txt
)

if [ -z "$DEBUG" ]; then
    pip3 install buildbot[bundle,tls] buildbot-pkg
else
    [ ! -d /app/buildbot ] &&
    (
        cd /app
        git clone -b v1.1.2 --single-branch --depth 1 https://github.com/buildbot/buildbot.git
    )
fi

[ -d /app/buildbot ] &&
(
    cd /app/buildbot/master
    python3 setup.py build install
    cd /app/buildbot/pkg
    python3 setup.py build install
    cd /app/buildbot/www/base
    python3 setup.py build install
    cd /app/buildbot/www/console_view
    python3 setup.py build install
)

[ -d /app/pullrequests ] &&
(
    cd /app/pullrequests
    python3 setup.py build install
)

(
    cd /app/config
    buildbot --verbose upgrade-master .
)
