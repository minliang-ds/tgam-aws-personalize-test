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

## Deploy ML Ops Steps


1. Start an AWS CloudShell session from the AWS console
1. Clone the project repo:
    - `git clone codecommit::us-east-1://amazon_personalize_streaming_events`
1. Navigate into the *mlops/personalize-step-functions* directory:
    - `cd mlops/personalize-step-functions`
1. Validate your SAM project:
    - `sam validate` 
1. Build your SAM project:
    - `sam build` 
1. Deploy your project. SAM offers a guided deployment option, note that you will need to provide your email address as a parameter to receive a notification.
    - `sam deploy --stack-name tgam-personalize-mlops-test  --s3-bucket sam-dev-sophi-bucket-us-east-1  --capabilities CAPABILITY_IAM  --parameter-overrides ParameterKey=Email,ParameterValue=mlinliu@amazon.com`
1. Navigate to your email inbox and confirm your subscription to the SNS topic
1. Once deployed, the pipeline will create the **InputBucket** which you can find in the CloudFormation stack output. Use it to upload your CSV datasets using the following structure:
```bash
Items/              # Items dataset(s) folder
Interactions/       # Interaction dataset(s) folder
``` 
1. Navigate into the *mlops* directory:
    - `cd ~/sagemaker_notebook_instance_test/mlops`
1. Upload the `params.json` file to the **root directory of the InputBucket**. This step will trigger the step functions workflow.
    - `aws s3 cp ./params.json s3://<input-bucket-name>`
1. Navigate to AWS Step Functions to monitor the workflow (Optional). Once the workflow completes successfully (which might take 12-15 hours), an email notification will be sent out.


## Deploy Recommendations API

1. Start an AWS CloudShell session from the AWS console
1. Clone the project repo:
```
git clone codecommit::us-east-1://amazon_personalize_streaming_events
```
1. Navigate into the *mlops/personalize-step-functions* directory:
```
cd api
```

1. Validate your SAM project:
```bash
sam validate
```

1. Build your SAM project:
```bash
sam build
```

1. Deploy your project. SAM offers a guided deployment option, note that you will need to provide your email address as a parameter to receive a notification.
```bash
sam deploy --stack-name tgam-personalize-api-test  --s3-bucket sam-dev-sophi-bucket-us-east-1  --capabilities CAPABILITY_IAM  \
    --parameter-overrides ParameterKey=EventTrackerIdParam,ParameterValue=f843d3d9-7153-436b-b4be-ed5ce8375c575fcf \
    --parameter-overrides ParameterKey=ContentDatasetName,ParameterValue=tgam-personalize-mlops-test \
    --parameter-overrides ParameterKey=CampaignName,ParameterValue=userPersonalizationCampaign \
    --parameter-overrides ParameterKey=FiltersPrefix,ParameterValue=tgam-personalize-mlops-test \ 
    --parameter-overrides ParameterKey=ContentDynamoDbTableName,ParameterValue=Sophi3ContentMetaData 
    
```

1. Update time for cloudwatch logs retation

1. Test api:
```bash
export api_endpoint=(url from output url)
export api_key=(api from output url)

  curl ${api_endpoint}/dev/recommendations \
  -H 'authority: recoapi-prd.theglobeandmail.ca' \
  -H 'content-type: application/json' \
  -H "x-api-key: ${api_key}" \
  --data-raw '{"sub_requests":[{"widget_id":"recommended-art_same_section_mostpopular","include_read":false,"include_content_types":"wire,news,blog,column,review,gallery","limit":10,"context":"art_same_section_mostpopular","width":"w620","include_sections":"canada","min_content_age":61,"platform":"desktop","max_content_age":345601,"rank":1,"last_content_ids":"4LTZGA2T7FA5FC3XJXTHCUGXLI","newsletter_ids":"","section":"/canada/","seo_keywords":"","visitor_type":"anonymous"}],"platform":"desktop","visitor_id":"42ed07db-c4d5-41e6-8e51-5173da2bfec0","hash_id":""}'  | jq
```



## 