#!/bin/bash
cfn-lint template.yml
sam validate
sam build 
sam deploy --stack-name tgam-personalize-api-test  --s3-bucket sam-dev-sophi-bucket-us-east-1  --capabilities CAPABILITY_IAM   --parameter-overrides ParameterKey=EventTrackerIdParam,ParameterValue=f843d3d9-7153-436b-b4be-ed5ce8375c57 ParameterKey=ContentDatasetName,ParameterValue=tgam-personalize-mlops-test ParameterKey=CampaignName,ParameterValue=userPersonalizationCampaign ParameterKey=StageName,ParameterValue=v1
