#!/bin/bash

set -x

addgroup -g $APP_GID appgroup
adduser -D -u $APP_UID -s /bin/bash -G appgroup appuser

mkdir -p /env
chown -R appuser:appgroup /env

mkdir -p /data
mkdir -p /data/builds
mkdir -p /data/db
mkdir -p /data/logs
chown appuser:appgroup /data /data/*

mkdir -p /builds
touch /builds/dummy
chown appuser:appgroup /builds /builds/*
