import time
import json
import os
import base64

from boto3 import client

from botocore import config as boto_config
from botocore.exceptions import ClientError
from aws_embedded_metrics import metric_scope

config = boto_config.Config(
    connect_timeout=1, read_timeout=1,
    retries={'max_attempts': 2})

enviroment            = os.environ.get('Environment')
resources_prefix      = os.environ.get('ResourcesPrefix')
filter_app_id         = os.environ.get('FilterAppId')
personalize_cli       = client('personalize-events', config=config)
dynamo_client         = client('dynamodb', config=config)
settings_dynamo_table =  f"{resources_prefix}-{enviroment}-api-settings"


def _get_dynamo_settings(db, dynamo_table):
    try:
        personalize_list = []
        scan_kwargs = {
            'TableName': dynamo_table,
            'FilterExpression': "#status = :active ",
            'ExpressionAttributeNames': {
                "#status": "status",
            },
            'ExpressionAttributeValues': {
                ":active": {
                    'S': "active"
                }
            }
        }

        done = False
        start_key = None
        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = db.scan(**scan_kwargs)
            personalize_list.extend(response.get('Items', []))
            start_key = response.get('LastEvaluatedKey', None)
            done = start_key is None

        return personalize_list

    except ClientError as e:
        print(f"Key Error: {e}")


@metric_scope
def handler(event, context, metrics):
    metrics.set_property("LambdaRequestId", context.aws_request_id)
    metrics.put_dimensions({"Type": "PutEvents"})
    settings = _get_dynamo_settings(dynamo_client, settings_dynamo_table)

    if len(settings) == 0:
        return {'statusCode': '500', 'body': json.dumps("No active trackers found in dynamo settings table")}

    status_code = "200"
    status_body = json.dumps("Success")

    success_events = 0
    fail_events = 0
    skip_events = 0

    for record in event['Records']:
        #Kinesis data is base64 encoded so decode here
        payload_str=base64.b64decode(record["kinesis"]["data"])
        payload = json.loads(payload_str)
        print("Decoded payload: " + str(payload))


        if (payload.get('Published') is not True):
            printf(f"Skipping content: invalid Published {payload.get('Published')}")
            skip_events += 1;
            continue

        exclude = 0

        if (payload.get('Sponsored') is True):
            exclude = 1
        elif (payload.get('Section') == "life/horoscopes"):
            exclude = 1
        elif ("zerocanada" in payload.get('Keywords', [])):
            exclude = 1
        elif ("omit" in payload.get('Keywords', [])):
            exclude = 1

        try:
            timestamp = int(round(time.mktime(time.strptime(payload.get('UpdatedDate')[:-5], '%Y-%m-%dT%H:%M:%S'))))
        except:
            timestamp = int(round(time.time()))

        putItemsParams = {
            'items': [
                {
                    'itemId': payload.get('ContentId'),
                    'properties': json.dumps({
                        'ContentText': payload.get('ContentText'),
                        'Category': payload.get('Category'),
                        'WordCount': payload.get('WordCount'),
                        'Published': payload.get('Published'),
                        'ContentType': payload.get('ContentType'),
                        'Exclude': exclude,
                        'CREATION_TIMESTAMP': timestamp,
                    })
                }
            ]
        }

        status_code = "200"
        status_body = json.dumps("Success")

        for tracker in settings:
            print(f"Put item to dataset {tracker.get('datasetArn').get('S')}")
            putItemsParams['datasetArn'] = tracker.get('datasetArn').get('S')
            print("This is the input object: " + str(putItemsParams))
            try:
                response = personalize_cli.put_items(**putItemsParams)
                print(f"put_items response: {response}")
            except ClientError as e:
                status_code = "500"
                status_body = f"Personalize Client Error: {e}"
                print(f"Personalize Client Error: {e}")
                fail_events += 1
            else:
                success_events += 1

    metrics.put_metric("SuccessItems", success_events, "None")
    metrics.put_metric("FailItems", fail_events, "None")
    metrics.put_metric("SkipItems", skip_events, "None")
    return {'statusCode': status_code, 'body': status_body}



