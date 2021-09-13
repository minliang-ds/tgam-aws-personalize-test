#!/bin/bash

CODEPIPELINE_STACK_NAME="tgam-personalize-test-streaming-events"
region="us-east-1"

set -eu

aws cloudformation create-stack \
        --capabilities CAPABILITY_IAM \
        --stack-name $CODEPIPELINE_STACK_NAME \
        --template-body file://pipeline.yaml \
        --parameters ParameterKey=DirectInternetAccess,ParameterValue="Enabled" \
        --parameters ParameterKey=NotebookName,ParameterValue="tgam-personalize-test" \
        --parameters ParameterKey=VolumeSize,ParameterValue="50"  \
        --parameters ParameterKey=BucketName,ParameterValue="tgam-personalize-test"
        
        
