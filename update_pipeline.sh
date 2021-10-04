#!/bin/bash

CODEPIPELINE_STACK_NAME="tgam-personalize-test-streaming-events"
region="us-east-1"
campain_arn="arn:aws:personalize:us-east-1:727304503525:campaign/personalize-poc6-userpersonalization"

set -eu

aws cloudformation update-stack \
        --capabilities CAPABILITY_IAM \
        --stack-name $CODEPIPELINE_STACK_NAME \
        --template-body file://pipeline.yaml \
        --parameters ParameterKey=RepoName,ParameterValue="amazon_personalize_streaming_events" \
        --parameters ParameterKey=RepoBranch,ParameterValue="development" \
        --parameters ParameterKey=CampaignARNParam,ParameterValue="${campain_arn}" 


while true; do

status=`aws cloudformation describe-stacks --stack-name ${CODEPIPELINE_STACK_NAME} --query 'Stacks[*].StackStatus' --output text`
echo ${status}

if [[ "${status}" ==  "UPDATE_COMPLETE" ]] || [[ "${status}" ==  "UPDATE_ROLLBACK_COMPLETE" ]] ; then
break
fi
sleep 1
done