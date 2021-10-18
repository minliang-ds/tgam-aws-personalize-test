#!/bin/bash
cfn-lint template.yml
sam validate
sam build 
sam deploy --stack-name tgam-personalize-mlops-test  --s3-bucket sam-dev-sophi-bucket-us-east-1  --capabilities CAPABILITY_IAM  --parameter-overrides ParameterKey=Email,ParameterValue=mlinliu@amazon.com