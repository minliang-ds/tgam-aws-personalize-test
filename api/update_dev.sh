#!/bin/bash

if [[ -n "${profile}" ]]; then
profile_arg="--profile ${profile}"
fi

stack_name="tgam-personalize-api-test"
deploy_region="us-east-1"

set -e 
cfn_nag_scan -i template.yml
cfn-lint template.yml
bandit -r api-lambdas/getRecommendations/
sam validate ${profile_arg}
sam build ${profile_arg}
sam deploy ${profile_arg} --stack-name ${stack_name}  \
  --force-upload \
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

