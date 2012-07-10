#!/bin/bash

# Set up an .s3cfg file for s3cmd from our Heroku environment variables.

if [ -z "$AWS_ACCESS_KEY_ID" -o -z "$AWS_SECRET_ACCESS_KEY" ] ;then
    echo Error: please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY >&2
    exit 1
fi

cat > ~/.s3cfg <<EOF
[default]
access_key = $AWS_ACCESS_KEY_ID
secret_key = $AWS_SECRET_ACCESS_KEY
EOF
