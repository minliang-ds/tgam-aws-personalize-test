#!/bin/bash
#set -x
CODEPIPELINE_STACK_NAME="tgam-personalize-test-streaming-events"
region="us-east-1"
campain_arn="arn:aws:personalize:us-east-1:727304503525:campaign/personalize-poc6-userpersonalization"
tracker_id="f19a3e78-4820-4634-ae77-3c9bde0f0b9a"
kinesis_arn="arn:aws:kinesis:us-east-1:727304503525:stream/sophi3-transformed-event-stream"
kinesis2_arn="arn:aws:kinesis:us-east-1:727304503525:stream/sophi3-unified-content-stream"
content_dataset_arn="arn:aws:personalize:us-east-1:727304503525:dataset/personalize-poc6/ITEMS"

set -eu

aws cloudformation update-stack \
        --capabilities CAPABILITY_IAM \
        --stack-name $CODEPIPELINE_STACK_NAME \
        --template-body file://pipeline.yaml \
        --parameters ParameterKey=RepoName,ParameterValue="amazon_personalize_streaming_events" \
         ParameterKey=RepoBranch,ParameterValue="development" \
         ParameterKey=CampaignARNParam,ParameterValue="${campain_arn}" \
         ParameterKey=EventTrackerIdParam,ParameterValue="${tracker_id}" \
         ParameterKey=ExistingKinesisStreamARN,ParameterValue="${kinesis_arn}" \
         ParameterKey=ExistingSecondaryKinesisStreamARN,ParameterValue="${kinesis2_arn}" \
         ParameterKey=ContentDatasetARN,ParameterValue="${content_dataset_arn}" \


while true; do

status=`aws cloudformation describe-stacks --stack-name ${CODEPIPELINE_STACK_NAME} --query 'Stacks[*].StackStatus' --output text`
echo ${status}

if [[ "${status}" ==  "UPDATE_COMPLETE" ]] || [[ "${status}" ==  "UPDATE_ROLLBACK_COMPLETE" ]] ; then
break
fi
sleep 1
done