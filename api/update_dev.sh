#!/bin/bash

if [[ -n "${profile}" ]]; then
profile_arg="--profile ${profile}"
fi

env="dev"
stack_name="tgam-personalize-api-dev"
deploy_region="us-east-1"

set -e 
cfn_nag_scan -i template.yaml
cfn-lint template.yaml
bandit -r api-lambdas/getRecommendations/
sam validate ${profile_arg}
sam build ${profile_arg}
sam deploy ${profile_arg} --stack-name ${stack_name}  \
  --force-upload \
  --region ${deploy_region} \
  --s3-bucket sam-${env}-sophi-bucket-us-east-1  \
  --capabilities CAPABILITY_IAM  \
  --tags "Environment=${env} CostAllocationProduct=amazon_personalize ManagedBy=CloudFormation" \
  --parameter-overrides \
  ParameterKey=ResourcesPrefix,ParameterValue=tgam-personalize \
  ParameterKey=DefaultNotificationEmail,ParameterValue="mlinliu@amazon.com" \
  ParameterKey=Environment,ParameterValue=${env} \
  ParameterKey=UpdateTimestamp,ParameterValue=$(date +"%s")

api_id=`aws cloudformation describe-stacks ${profile_arg} --stack-name ${stack_name}  --region ${deploy_region} --query 'Stacks[0].Outputs' --output text | grep ^ApiId | awk {'print $2'}`
stage_name=`aws cloudformation describe-stacks ${profile_arg} --stack-name ${stack_name}  --region ${deploy_region} --query 'Stacks[0].Outputs' --output text | grep ^StageName | awk {'print $2'}`
api_url=`aws cloudformation describe-stacks ${profile_arg} --stack-name ${stack_name}  --region ${deploy_region} --query 'Stacks[0].Outputs' --output text | grep ^POSTRecommendationsApiGatewayInvokeURL | awk {'print $2'}`

aws apigateway create-deployment ${profile_arg} \
    --region ${deploy_region} \
    --rest-api-id ${api_id} \
    --stage-name ${stage_name}

echo "Test api: ${api_url}"
curl ${api_url} -H 'Content-Type: application/json' --data-raw '{"visitor_id":"e63cdc7c-742f-4442-8a24-a1cd1f36c8b0","platform":"desktop","sub_requests":[{"widget_id":"recommended-mobile_art_morestories","last_content_ids":"TTSIR6HFKZC5FNS3MSMZN7ZS3I","limit":6,"context":"mobile_art_morestories","platform":"desktop","section":"/canada/alberta/","visitor_type":"anonymous"}]}' -v

