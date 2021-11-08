#!/bin/bash

if [[ -n "${profile}" ]]; then
profile_arg="--profile ${profile}"
fi

env="dev"
stack_name="tgam-personalize-mlops-${env}"
pipeline_name="tgam-personalize-${env}-api-pipeline"
deploy_region="us-east-1"


set -e
s3_bucket=`aws cloudformation describe-stacks --stack-name ${pipeline_name}  ${profile_arg} --region ${deploy_region} --query 'Stacks[0].Outputs' --output text  | grep PipelineArtifactsBucket | awk {'print $2'}`

cd personalize-step-functions 
cfn-lint template.yaml
cfn_nag_scan -i template.yaml
sam validate ${profile_arg}
sam build ${profile_arg}
sam deploy ${profile_arg} --stack-name ${stack_name}  \
  --force-upload \
  --s3-bucket ${s3_bucket} \
  --capabilities CAPABILITY_IAM  \
  --tags "Environment=${env} CostAllocationProduct=amazon_personalize ManagedBy=CloudFormation" \
  --parameter-overrides \
  ParameterKey=ResourcesPrefix,ParameterValue=tgam-personalize \
  ParameterKey=Environment,ParameterValue=${env}



input_bucket=`aws cloudformation describe-stacks ${profile_arg} --stack-name ${stack_name}  --region ${deploy_region} --query 'Stacks[0].Outputs' --output table | grep InputBucketName  | awk -F \| {'print $4'} | awk {'print $1'}`
aws s3 cp s3://${input_bucket}/params.json .temp_params.json ${profile_arg}  || true
echo "Diff params.json compare to s3://${input_bucket}/params.json "
diff -ruNp ../params.json .temp_params.json || true

echo "If needed run:"
echo aws s3 cp params.json s3://${input_bucket}/params.json ${profile_arg}
