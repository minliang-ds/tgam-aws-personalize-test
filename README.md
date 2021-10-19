# MLOps pipeline for Amazon Personalize Recommender System

This pipeline builds a User-Personalization Amazon Personalize campaign for Sophi from scatch, assuming input datasets have been pre-generated. As shown in the following architecture diagram, the pipeline uses AWS Serverless Application Model (SAM) to deploy an AWS Step Function Workflow containing AWS Lambda functions that call Amazon S3, Amazon Personalize, and Amazon SNS APIs.

The below diagram describes the architecture of the solution:

![Architecture Diagram](images/architecture.png)

The below diagram showcases the StepFunction workflow definition:

![stepfunction definition](images/stepfunctions.png)





## Global Steps Steps

1. Create S3 bucket to keep configuration for SAM deployments
```bash
export env="dev"
aws s3api create-bucket --bucket sam-${env}-sophi-bucket-us-east-1 --region us-east-1

```

## Deploy Personalize CloudFormation Dashboard
1. Start an AWS CloudShell session from the AWS console
2. Clone the project repo:
```bash
git clone codecommit::us-east-1://amazon_personalize_streaming_events
```
3. Navigate into the *monitoring* directory:
```bash
cd monitoring
```
4. Validate your SAM project:
```bash
sam validate
```
5. Build your SAM project:
```bash
sam build
```
6. Deploy your project. SAM offers a guided deployment option, note that you will need to provide your email address as a parameter to receive a notification.
```bash
sam deploy --stack-name tgam-personalize-monitoring-test  --s3-bucket sam-dev-sophi-bucket-us-east-1  --capabilities CAPABILITY_IAM  \
--parameter-overrides ParameterKey=CampaignARNs,ParameterValue=all \
ParameterKey=Regions,ParameterValue=us-east-1 \
ParameterKey=NotificationEndpoint,ParameterValue=mlinliu@amazon.com 
````



## Deploy ML Ops Steps

1. Start an AWS CloudShell session from the AWS console
2. Clone the project repo:
```bash
git clone codecommit::us-east-1://amazon_personalize_streaming_events
```
3. Navigate into the *mlops/personalize-step-functions* directory:
```bash
cd mlops/personalize-step-functions
```
4. Validate your SAM project:
```bash
sam validate
```
5. Build your SAM project:
```bash
sam build
```
6. Deploy your project. SAM offers a guided deployment option, note that you will need to provide your email address as a parameter to receive a notification.
```bash
sam deploy --stack-name tgam-personalize-mlops-test  --s3-bucket sam-dev-sophi-bucket-us-east-1  --capabilities CAPABILITY_IAM  --parameter-overrides ParameterKey=Email,ParameterValue=mlinliu@amazon.com
````
7. Navigate to your email inbox and confirm your subscription to the SNS topic
8. Once deployed, the pipeline will create the **InputBucket** which you can find in the CloudFormation stack output. Use it to upload your CSV datasets using the following structure:
```bash
Items/              # Items dataset(s) folder
Interactions/       # Interaction dataset(s) folder
``` 
9. Navigate into the *mlops* directory:
```bash
cd ~/sagemaker_notebook_instance_test/mlops
```
10. Upload the `params.json` file to the **root directory of the InputBucket**. This step will trigger the step functions workflow.
```bash
aws s3 cp ./params.json s3://<input-bucket-name>
```
11. Navigate to AWS Step Functions to monitor the workflow (Optional). Once the workflow completes successfully (which might take 12-15 hours), an email notification will be sent out.


## Deploy Recommendations API
1. Start an AWS CloudShell session from the AWS console
2. Clone the project repo:
```bash
git clone codecommit::us-east-1://amazon_personalize_streaming_events
```

3. Navigate into the *mlops/personalize-step-functions* directory:
```bash
cd api
```

4. Validate your SAM project:
```bash
sam validate
```

5. Build your SAM project:
```bash
sam build
```

6. Deploy your project. SAM offers a guided deployment option, note that you will need to provide your email address as a parameter to receive a notification.
```bash
sam deploy --stack-name tgam-personalize-api-test  --s3-bucket sam-dev-sophi-bucket-us-east-1  --capabilities CAPABILITY_IAM  \
    --parameter-overrides ParameterKey=EventTrackerIdParam,ParameterValue=f843d3d9-7153-436b-b4be-ed5ce8375c575fcf \ 
ParameterKey=ContentDatasetName,ParameterValue=tgam-personalize-mlops-test \
ParameterKey=CampaignName,ParameterValue=userPersonalizationCampaign \
ParameterKey=FiltersPrefix,ParameterValue=tgam-personalize-mlops-test \ 
ParameterKey=ContentDynamoDbTableName,ParameterValue=Sophi3ContentMetaData 
```

7. Update time for cloudwatch logs retation

8. Test api:
```bash
export api_endpoint=(url from output url)
export api_key=(api from output url)

  curl ${api_endpoint}/dev/recommendations \
  -H 'authority: recoapi-prd.theglobeandmail.ca' \
  -H 'content-type: application/json' \
  -H "x-api-key: ${api_key}" \
  --data-raw '{"sub_requests":[{"widget_id":"recommended-art_same_section_mostpopular","include_read":false,"include_content_types":"wire,news,blog,column,review,gallery","limit":10,"context":"art_same_section_mostpopular","width":"w620","include_sections":"canada","min_content_age":61,"platform":"desktop","max_content_age":345601,"rank":1,"last_content_ids":"4LTZGA2T7FA5FC3XJXTHCUGXLI","newsletter_ids":"","section":"/canada/","seo_keywords":"","visitor_type":"anonymous"}],"platform":"desktop","visitor_id":"42ed07db-c4d5-41e6-8e51-5173da2bfec0","hash_id":""}'  | jq
```



## Api documentation

## Request Fields

## Reply Fields

## Data convertion between dynamoDB and reply
| Field in DynamoDB | Field in reply | Additional convertion | Comment | 
| ----------------- | -------------- | --------------------- |-------- | 
| Byline | byline | from list of string to string (first element from list) |

- 
## Frontend fields requiremetns
published_at - String
updated_at - String
url - String
title - String
deck - String
byline - String
content_type - String
protection_product - String
label - String
article.author_rel[0].url220
article.promo_image.urls["220"]
article.picture_rel[0].url220
