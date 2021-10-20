#!/bin/bash
cfn-lint template.yaml
sam validate
sam build 
sam deploy --stack-name tgam-personalize-monitoring-test  --s3-bucket sam-dev-sophi-bucket-us-east-1  --capabilities CAPABILITY_IAM  --parameter-overrides ParameterKey=CampaignARNs,ParameterValue=all ParameterKey=Regions,ParameterValue=us-east-1 ParameterKey=NotificationEndpoint,ParameterValue=mlinliu@amazon.com
