#!/bin/bash
# create the lambda function, package and upload upload the source code and schedule invocations

source package.sh

aws lambda create-function \
    --function-name archive-mo-covid-data \
    --zip-file fileb://package.zip \
    --handler function.lambda_handler \
    --runtime python3.8 \
    --role arn:aws:iam::796077402566:role/mo-covid-dashboard-archiver \
    --timeout 120 \
    > 'function.json'

rm package.zip

source schedule.sh
