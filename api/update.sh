#!/bin/bash

set -e 
cfn-lint template.yml
bandit -r api-lambdas/getRecommendations/
sam validate
sam build 
sam deploy --stack-name tgam-personalize-api-test  \
  --s3-bucket sam-dev-sophi-bucket-us-east-1  \
  --capabilities CAPABILITY_IAM  \
  --parameter-overrides \
  ParameterKey=ResourcesPrefix,ParameterValue=tgam-personalize \
  ParameterKey=Environment,ParameterValue=dev \
  ParameterKey=StageName,ParameterValue=v1 \
  ParameterKey=CostAllocationProduct,ParameterValue=amazon_personalize \
  ParameterKey=KinesisContentStream,ParameterValue=sophi3-unified-content-stream \
  ParameterKey=KinesisEventStream,ParameterValue=sophi3-transformed-event-stream \
  ParameterKey=LogRotation,ParameterValue=30 \
  ParameterKey=ContentDatasetName,ParameterValue=tgam-personalize-mlops-test \
  ParameterKey=EventTrackerIdParam,ParameterValue=f843d3d9-7153-436b-b4be-ed5ce8375c57 \
  ParameterKey=EventTrackerArn,ParameterValue=arn:aws:personalize:us-east-1:727304503525:event-tracker/7a1a2aff \
  ParameterKey=CampainProvisionedTPS,ParameterValue=1 \
  ParameterKey=CampaignName,ParameterValue=userPersonalizationCampaign \
  ParameterKey=FiltersPrefix,ParameterValue=tgam-personalize-mlops-test \
  ParameterKey=Sophi3DynamoDbTableName,ParameterValue=Sophi3ContentMetaData \
  ParameterKey=Sophi2DynamoDbTableName,ParameterValue=arc_content \
  ParameterKey=ExternalDomain,ParameterValue=recoapi-ng-dev.theglobeandmail.ca \
  ParameterKey=CertificateARN,ParameterValue=arn:aws:acm:us-east-1:727304503525:certificate/2d541648-2f71-4b97-89ed-26d252d496b9 \
  ParameterKey=DefaultNotificationEmail,ParameterValue=mlinliu@amazon.com
  
