#!/bin/bash
# package and upload the source code

source package.sh

aws lambda update-function-code \
    --function-name archive-mo-covid-data \
    --zip-file fileb://package.zip \
    > 'function.json'

rm package.zip
