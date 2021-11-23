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

    success_events = 0
    fail_events = 0
    skip_events = 0

    for record in event['Records']:
        #Kinesis data is base64 encoded so decode here
        payload_str=base64.b64decode(record["kinesis"]["data"])
        payload = json.loads(payload_str)
        #print("Decoded payload: " + str(payload.get('sp_event_id')))

        if (payload.get('sp_event_id') is None):
            printf(f"Skipping event: invalid sp_event_id {payload.get('sp_event_id')}")
            skip_events += 1;
            continue

        if (payload.get('sp_derived_tstamp') is None) or len(payload.get('sp_derived_tstamp').strip()) == 0:
            print(f"Skipping event: invalid sp_derived_tstamp: {payload.get('sp_derived_tstamp')}")
            skip_events += 1;
            continue

        if (payload.get('sp_app_id') is None) or payload.get('sp_app_id') != filter_app_id:
            print(f"Skipping event: invalid sp_app_id: {payload.get('sp_app_id')}")
            skip_events += 1;
            continue

        if (payload.get('content_contentId') is None) or len(payload.get('content_contentId').strip()) == 0:
            print(f"Skipping event: invalid content_contentId: {payload.get('content_contentId')}")
            skip_events += 1;
            continue

        if (payload.get('page_type') is None) or payload.get('page_type') != "article":
            print(f"Skipping event: invalid page_type: {payload.get('page_type')}")
            skip_events += 1;
            continue

        if (payload.get('sp_event_name') is None) or payload.get('sp_event_name') != "page_view":
            print(f"Skipping event: invalid sp_event_name: {payload.get('sp_event_name')}")
            skip_events += 1;
            continue

        if (payload.get('sp_domain_sessionid') is None):
            print(f"Skipping event: invalid sp_domain_sessionid {payload.get('sp_domain_sessionid')}")
            skip_events += 1;
            continue

        if (payload.get('sp_user_id') is None or (len(payload.get('sp_user_id').strip()) == 0)) and (payload.get('sp_domain_userid') is None or (len(payload.get('sp_domain_userid').strip()) == 0)):
            print(f"Skipping event: invalid content_contentId: {payload.get('content_contentId')}")
            skip_events += 1;
            continue

        if ((payload.get('sp_user_id') is not None) and len(payload.get('sp_user_id').strip()) > 0):
            user_id = payload.get('sp_user_id')
        if ((payload.get('sp_domain_userid') is not None) or len(payload.get('sp_domain_userid').strip()) > 1):
            user_id = payload.get('sp_domain_userid')

        try:
            timestamp = int(round(time.mktime(time.strptime(payload.get('sp_derived_tstamp')[:-5], '%Y-%m-%dT%H:%M:%S'))))
        except:
            timestamp = int(round(time.time()))

        putEventsParams = {
            'sessionId': payload.get('sp_domain_sessionid'),
            'userId': user_id,
            'eventList': [{
                'eventId': payload.get('sp_event_id'),
                'eventType':  payload.get('sp_event_name'),
                'itemId':  payload.get('content_contentId'),
                'sentAt':  timestamp,
                'properties':  json.dumps({
                    'visitor_type': payload.get('visitor_type'),
                    'visitor_countryCode': payload.get('visitor_countryCode'),
                    'device_detector_visitorPlatform': payload.get('device_detector_visitorPlatform'),
                    'device_detector_brandName': payload.get('device_detector_brandName'),
                    'device_detector_browserFamily': payload.get('device_detector_browserFamily'),
                })
            }]
        }

        if (payload.get('page_rid') is not None):
            putEventsParams['eventList'][0]['recommendationId'] = payload.get('page_rid')

        status_code = "200"
        status_body = json.dumps("Success")

        for tracker in settings:
            print(f"Put event to tracker {tracker.get('eventTrackerId').get('S')}")
            putEventsParams['trackingId'] = tracker.get('eventTrackerId').get('S')
            print("This is the input object: " + str(putEventsParams))
            try:
                personalize_cli.put_events(**putEventsParams)
            except ClientError as e:
                status_code = "500"
                status_body = f"Personalize Client Error: {e}"
                print(f"Personalize Client Error: {e}")
                fail_events += 1
            else:
                success_events += 1

    metrics.put_metric("SuccessEvents", success_events, "None")
    metrics.put_metric("FailEvents", fail_events, "None")
    metrics.put_metric("SkipEvents", skip_events, "None")
    return {'statusCode': status_code, 'body': status_body}



