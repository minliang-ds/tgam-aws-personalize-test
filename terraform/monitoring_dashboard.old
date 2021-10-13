resource "aws_iam_role" "put_event" {
  name = "${local.resource_prefix}-put-event-${data.aws_region.current.name}"

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


resource "aws_iam_role_policy_attachment" "put_event_cloudwatch" {
  role       = aws_iam_role.put_event.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchFullAccess"
}

resource "aws_iam_role_policy_attachment" "put_event_execution_policy" {
  role       = aws_iam_role.put_event.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "put_event_kinesis_policy" {
  role       = aws_iam_role.put_event.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaKinesisExecutionRole"
}

# See also the following AWS managed policy: AWSLambdaBasicExecutionRole
resource "aws_iam_policy" "put_event" {
  name        = "${local.resource_prefix}-put_event-${data.aws_region.current.name}"
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
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "put_event" {
  role       = aws_iam_role.put_event.name
  policy_arn = aws_iam_policy.put_event.arn
}

data "archive_file" "put_event" {
  type        = "zip"
  output_path = "${path.module}/putevents.zip"
  source_dir  = "${path.module}/lambdas/putevents"
}

resource "aws_lambda_function" "put_event" {
  depends_on = [data.archive_file.put_event]

  filename      = data.archive_file.put_event.output_path
  function_name = "${local.resource_prefix}-put-event-${data.aws_region.current.name}"
  role          = aws_iam_role.put_event.arn
  handler       = "putevents.handler"

  source_code_hash = data.archive_file.put_event.output_base64sha256
  runtime          = "nodejs12.x"

  #timeout     = 35
  #memory_size = 1024
  environment {
    variables = {
      Environment         = var.Environment
      CurretnAccountId    = data.aws_caller_identity.current.account_id
      TRACKING_ID         = var.TrackingId
      CONTENT_DATASET_ARN = var.DataSetArn
    }
  }
}

resource "aws_cloudwatch_log_group" "put_event" {
  name              = "/aws/lambda/${aws_lambda_function.put_event.id}"
  retention_in_days = 30
}


resource "aws_lambda_event_source_mapping" "kinesis_lambda_event_mapping" {
  batch_size        = 100
  event_source_arn  = data.aws_kinesis_stream.put_event.arn
  enabled           = true
  function_name     = aws_lambda_function.put_event.arn
  starting_position = "TRIM_HORIZON"
}

data "aws_kinesis_stream" "put_event" {
  name = var.KinesisEventStream
}