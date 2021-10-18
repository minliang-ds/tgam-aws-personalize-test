resource "aws_iam_role" "iam_for_lambda_get_recommendations" {
  name = "${local.resource_prefix}-get-recommendations-${data.aws_region.current.name}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "get_recommendations_personzlize" {
  role       = aws_iam_role.iam_for_lambda_get_recommendations.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonPersonalizeFullAccess"
}


resource "aws_iam_role_policy_attachment" "get_recommendations_cloudwatch" {
  role       = aws_iam_role.iam_for_lambda_get_recommendations.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchFullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_execution_policy_role" {
  role       = aws_iam_role.iam_for_lambda_get_recommendations.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# See also the following AWS managed policy: AWSLambdaBasicExecutionRole
resource "aws_iam_policy" "lambda_execution_policy" {
  name        = "${local.resource_prefix}-get_recommendations-${data.aws_region.current.name}"
  path        = "/"
  description = "IAM policy for logging from a lambda"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "personalize:*"
      ],
      "Resource": "*",
      "Effect": "Allow"
    },
    {
      "Action": [
          "kinesis:SubscribeToShard",
          "kinesis:ListShards",
          "kinesis:GetShardIterator",
          "kinesis:GetRecords",
          "kinesis:DescribeStream",
          "kinesis:DescribeStreamSummary"
      ],
      "Resource": "*",
      "Effect": "Allow"
    },
    {
      "Action": [
          "dynamodb:BatchGetItem"
      ],
      "Resource": "${var.DynamoDbTableArn}",
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.iam_for_lambda_get_recommendations.name
  policy_arn = aws_iam_policy.lambda_execution_policy.arn
}

data "archive_file" "get_recommendations" {
  type        = "zip"
  output_path = "${path.module}/getRecommendations.zip"
  source_dir  = "${path.module}/lambdas/getRecommendations"
}

resource "aws_lambda_function" "get_recommendations_lambda" {
  depends_on = [data.archive_file.get_recommendations]

  filename      = data.archive_file.get_recommendations.output_path
  function_name = "${local.resource_prefix}-get-recommendations-${data.aws_region.current.name}"
  role          = aws_iam_role.iam_for_lambda_get_recommendations.arn
  handler       = "getRecommendations.handler"

  source_code_hash = data.archive_file.get_recommendations.output_base64sha256
  runtime          = "python3.8"

  timeout     = 35
  memory_size = 1024
  environment {
    variables = {
      Environment       = var.Environment
      FiltersPrefix     = var.FiltersPrefix
      CurretnAccountId  = data.aws_caller_identity.current.account_id
      CAMPAIGN_ARN      = var.CampainArn
      DynamoDbTableName = element(split("/", var.DynamoDbTableArn),1)
    }
  }
}

resource "aws_cloudwatch_log_group" "lambda-logx" {
  name              = "/aws/lambda/${aws_lambda_function.get_recommendations_lambda.id}"
  retention_in_days = 30
}

resource "aws_api_gateway_rest_api" "get_recommendations" {
  name        = "${local.resource_prefix}-get-recommendations-${data.aws_region.current.name}"
  description = "Get Recommendations api"
}

#Get content
resource "aws_iam_role" "iam_for_lambda_api_get_recommendations" {
  name = "${local.resource_prefix}-api-get-recommendations-${data.aws_region.current.name}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "apigateway.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}


# See also the following AWS managed policy: AWSLambdaBasicExecutionRole
#resource "aws_iam_policy" "api_dynamodb" {
#  name        = "${local.resource_prefix}-api-get-recommendations-${data.aws_region.current.name}"
#  path        = "/"
#  description = "IAM policy for API Gateway"
#
#  policy = <<EOF
#{
#  "Version": "2012-10-17",
#  "Statement": [
#    {
#      "Action": [
#          "dynamodb:Query"
#      ],
#      "Resource": "${var.DynamoDbTableArn}",
#      "Effect": "Allow"
#    }
#  ]
#}
#EOF
#}

#resource "aws_iam_role_policy_attachment" "api_dynamodb" {
#  role       = aws_iam_role.iam_for_lambda_api_get_recommendations.name
#  policy_arn = aws_iam_policy.api_dynamodb.arn
#}

                  
#resource "aws_api_gateway_resource" "get_content" {
#  rest_api_id = aws_api_gateway_rest_api.get_recommendations.id
#  parent_id   = aws_api_gateway_rest_api.get_recommendations.root_resource_id
#  path_part   = "content"
#}

#resource "aws_api_gateway_resource" "get_content_id" {
#  rest_api_id = aws_api_gateway_rest_api.get_recommendations.id
#  parent_id   = aws_api_gateway_resource.get_content.id
#  path_part   = "{ContentId}"
#}

#resource "aws_api_gateway_method" "get_content" {
#  rest_api_id      = aws_api_gateway_rest_api.get_recommendations.id
#  resource_id      = aws_api_gateway_resource.get_content_id.id
#  http_method      = "POST"
#  authorization    = "NONE"
#  api_key_required = true
#}

#resource "aws_api_gateway_integration" "get_content" {
#  rest_api_id = aws_api_gateway_rest_api.get_recommendations.id
#  resource_id = aws_api_gateway_method.get_content.resource_id
#  http_method = aws_api_gateway_method.get_content.http_method

#  integration_http_method = "ANY"
#  type                    = "AWS"
#  uri                     = "arn:aws:apigateway:${data.aws_region.current.name}:dynamodb:action/Query"
#  credentials             = aws_iam_role.iam_for_lambda_api_get_recommendations.arn
#  passthrough_behavior    = "WHEN_NO_TEMPLATES"
  
#  request_templates = {
#    "application/json" = <<EOF
#{
#    "TableName": "${element(split("/", var.DynamoDbTableArn),1)}",
#    "KeyConditionExpression": "#kn0 = :v1",
#    "ExpressionAttributeNames": {
#		  "#kn0": "ContentId"
#	  },
#    "ExpressionAttributeValues": {
#        ":v1": {
#            "S": "$input.params('ContentId')"
#        }
#    }
#}
#EOF
#  }
#  
#}

#resource "aws_api_gateway_integration_response" "get_content" {
#  rest_api_id = aws_api_gateway_rest_api.get_recommendations.id
#  resource_id = aws_api_gateway_method.get_content.resource_id
#  http_method = aws_api_gateway_method.get_content.http_method
#  status_code = "200"
#
#  response_templates = {
#    "application/json" = <<EOF
##set($inputRoot = $input.path('$'))
#{
#    "comments": [
#        #foreach($elem in $inputRoot.Items) {
#            "ContentId": "$elem.ContentId.S",
#            "AppId": "$elem.AppId.S",
#            "Category": "$elem.Category.S"
#        }#if($foreach.hasNext),#end
#	#end
#    ]
#}
#EOF
#  }
#}

#resource "aws_api_gateway_method_response" "get_content" {
#  rest_api_id = aws_api_gateway_rest_api.get_recommendations.id
#  resource_id = aws_api_gateway_method.get_content.resource_id
#  http_method = aws_api_gateway_method.get_content.http_method
#  status_code = "200"
#}


resource "aws_api_gateway_resource" "get_recommendations" {
  rest_api_id = aws_api_gateway_rest_api.get_recommendations.id
  parent_id   = aws_api_gateway_rest_api.get_recommendations.root_resource_id
  path_part   = "recommendations"
}

resource "aws_api_gateway_method" "get_recommendations" {
  rest_api_id      = aws_api_gateway_rest_api.get_recommendations.id
  resource_id      = aws_api_gateway_resource.get_recommendations.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "get_recommendations" {
  rest_api_id = aws_api_gateway_rest_api.get_recommendations.id
  resource_id = aws_api_gateway_method.get_recommendations.resource_id
  http_method = aws_api_gateway_method.get_recommendations.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_recommendations_lambda.invoke_arn
}

resource "aws_api_gateway_model" "get_recommendations" {
  rest_api_id  = aws_api_gateway_rest_api.get_recommendations.id
  name         = "recoomendations"
  description  = "a JSON schema"
  content_type = "application/json"

  schema = <<EOF
{}
EOF

}

resource "aws_api_gateway_deployment" "get_recommendations" {
  depends_on = [
    aws_api_gateway_integration.get_recommendations
  ]

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_rest_api.get_recommendations.body,
      aws_api_gateway_resource.get_recommendations.id
      
      ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  rest_api_id = aws_api_gateway_rest_api.get_recommendations.id
  stage_name  = "dev"
}



resource "aws_lambda_permission" "get_recommendations_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_recommendations_lambda.function_name
  principal     = "apigateway.amazonaws.com"

  # The /*/* portion grants access from any method on any resource
  # within the API Gateway "REST API".
  source_arn = "${aws_api_gateway_rest_api.get_recommendations.execution_arn}/*/*"
}

resource "aws_api_gateway_api_key" "get_recommendations" {
  name = "${local.resource_prefix}-get-recommendations-${data.aws_region.current.name}"
}

resource "aws_api_gateway_usage_plan" "get_recommendations" {
  name = "my_usage_plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.get_recommendations.id
    stage  = aws_api_gateway_deployment.get_recommendations.stage_name
  }
}

resource "aws_api_gateway_usage_plan_key" "main" {
  key_id        = aws_api_gateway_api_key.get_recommendations.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.get_recommendations.id
}

output "get_recommendations_url" {
  value = aws_api_gateway_deployment.get_recommendations.invoke_url
}

output "get_recommendations_api_key" {
  value     = aws_api_gateway_api_key.get_recommendations.value
  sensitive = true
}