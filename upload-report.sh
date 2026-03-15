#!/bin/bash

SERVER="195.35.33.159"
PORT="65002"
USER="u650112933"
REMOTE_DIR="~/public_html/webperf/reports"

FILE="$1"

if [ -z "$FILE" ]; then
    FILE=$(ls -t reports/*.html 2>/dev/null | head -n 1)
fi

if [ -z "$FILE" ]; then
    echo "No HTML report found."
    exit 1
fi

echo "Uploading: $FILE"
scp -P $PORT "$FILE" $USER@$SERVER:$REMOTE_DIR