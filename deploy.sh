#!/bin/bash
cd "$( dirname "${BASH_SOURCE[0]}" )"

# Settings
if [ ! -f deploy/env.sh ]; then
  cat > deploy/env.sh <<EOF
export APP_UID=$UID
export APP_GID=$GROUPS
EOF
fi

# Docker image
docker build -t buildbot_image deploy

echo "1) Check settings: deploy/env.sh, workers.json, users.json"

echo "2) Run command below to create docker container: "
echo "   docker run -it \
-p 8010:8010 -p 9989:9989 \
--name buildbot \
-v $(pwd):/app \
buildbot_image"
