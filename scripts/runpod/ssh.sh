#!/bin/zsh
exec ssh -i ~/.ssh/runpod_soundbath -o StrictHostKeyChecking=no -o ConnectTimeout=15 -o LogLevel=ERROR -p 25694 root@47.47.180.34 "$@"
