#!/bin/bash

stack_name="tgam-personalize-api-test"
deploy_region="us-east-1"

set -e 
cfn_nag_scan -i template.yml
cfn-lint template.yml
bandit -r api-lambdas/getRecommendations/
sam validate
sam build 
sam deploy --stack-name ${stack_name}  \
  --region ${deploy_region} \
  --s3-bucket sam-dev-sophi-bucket-us-east-1  \
  --capabilities CAPABILITY_IAM  \
  --tags "Environment=dev CostAllocationProduct=amazon_personalize ManagedBy=CloudFormation" \
  --parameter-overrides \
  ParameterKey=ResourcesPrefix,ParameterValue=tgam-personalize \
  ParameterKey=DefaultNotificationEmail,ParameterValue="mlinliu@amazon.com" \
  ParameterKey=Environment,ParameterValue=dev \
  ParameterKey=LambdaVPC,ParameterValue=vpc-0a53827efb39f973f \
  ParameterKey=LambdaPrivateSubnetIDs,ParameterValue="subnet-0efb9d6d3ea5016f9,subnet-0c7691b437e67ca01,subnet-02f1cad54fa47455c,subnet-08e56efdbcd9d5d6b" \
  ParameterKey=CertificateARN,ParameterValue=arn:aws:acm:us-east-1:727304503525:certificate/b6598508-3ff5-46ab-8099-4b802e625711 \
  ParameterKey=ContentDatasetName,ParameterValue=tgam-personalize-mlops-test \
  ParameterKey=EventTrackerIdParam,ParameterValue=f843d3d9-7153-436b-b4be-ed5ce8375c57 \
  ParameterKey=EventTrackerArn,ParameterValue=arn:aws:personalize:us-east-1:727304503525:event-tracker/7a1a2aff \
  ParameterKey=CampaignProvisionedTPS,ParameterValue=10 \
  ParameterKey=CampaignName,ParameterValue=userPersonalizationCampaign \
  ParameterKey=FiltersPrefix,ParameterValue=tgam-personalize-mlops-test

api_id=`aws cloudformation describe-stacks --stack-name ${stack_name}  --region ${deploy_region} --query 'Stacks[0].Outputs' --output text | grep ^ApiId | awk {'print $2'}`
stage_name=`aws cloudformation describe-stacks --stack-name ${stack_name}  --region ${deploy_region} --query 'Stacks[0].Outputs' --output text | grep ^StageName | awk {'print $2'}`

aws apigateway create-deployment \
    --region ${deploy_region} \
    --rest-api-id ${api_id} \
    --stage-name ${stage_name}
