#!/bin/bash

aws events remove-targets \
    --rule mo-covid-archive-rule \
    --ids 1

aws lambda remove-permission \
    --function-name archive-mo-covid-data \
    --statement-id mo-covid-archive-statement

aws events delete-rule \
    --name mo-covid-archive-rule

aws lambda delete-function \
    --function-name archive-mo-covid-data

rm event-rule.json
rm function.json
