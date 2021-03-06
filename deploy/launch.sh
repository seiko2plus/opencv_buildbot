#!/bin/bash

umask 0000
. /env/bin/activate

cd /app/config

if [ -f /app/deploy/env.sh ]; then
	. /app/deploy/env.sh
fi

if [ -z "$DEBUG" ]; then
	buildbot --verbose start --nodaemon
else
	python3 /app/deploy/run_debug.py --verbose start --nodaemon
fi
