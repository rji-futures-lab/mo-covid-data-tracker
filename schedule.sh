#!/bin/bash
# schedule invocations of the lambda function

aws events put-rule \
    --name mo-covid-archive-rule \
    --schedule-expression 'rate(5 minutes)' \
    > 'event-rule.json'

aws lambda add-permission \
    --function-name archive-mo-covid-data \
    --statement-id mo-covid-archive-statement \
    --action 'lambda:InvokeFunction' \
    --principal events.amazonaws.com \
    --source-arn $(cat 'event-rule.json' | jq -r '.RuleArn')

aws events put-targets \
    --rule mo-covid-archive-rule \
    --targets "Id"="1","Arn"=$(cat 'function.json' | jq -r '.FunctionArn')
