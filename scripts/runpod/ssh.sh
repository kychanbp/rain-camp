#!/bin/zsh
exec ssh -i ~/.ssh/runpod_soundbath -o StrictHostKeyChecking=no -o ConnectTimeout=15 -o LogLevel=ERROR -p 27718 root@103.196.86.118 "$@"
