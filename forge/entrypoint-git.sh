#!/bin/bash
# Forge Worker Entrypoint — configures git credentials before starting worker

if [ -n "$GH_TOKEN" ]; then
    echo "https://forge-worker:${GH_TOKEN}@github.com" > /home/pmos/.git-credentials
    git config --global credential.helper "store --file=/home/pmos/.git-credentials"
    echo "[entrypoint] Git credentials configured"
fi

exec "$@"
