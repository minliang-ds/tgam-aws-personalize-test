#!/bin/bash

CODEPIPELINE_STACK_NAME="tgam-personalize-test-streaming-events"
region="us-east-1"

set -eu

aws cloudformation create-stack \
        --capabilities CAPABILITY_IAM \
        --stack-name $CODEPIPELINE_STACK_NAME \
        --template-body file://pipeline.yaml \
        --parameters ParameterKey=RepoName,ParameterValue="amazon_personalize_streaming_events" \
        --parameters ParameterKey=RepoBranch,ParameterValue="development" 


while true; do

status=`aws cloudformation describe-stacks --stack-name ${CODEPIPELINE_STACK_NAME} --query 'Stacks[*].StackStatus' --output text`
echo ${status}

if [[ "${status}" ==  "UPDATE_COMPLETE" ]] || [[ "${status}" ==  "UPDATE_ROLLBACK_COMPLETE" ]] ; then
break
fi
sleep 1
done