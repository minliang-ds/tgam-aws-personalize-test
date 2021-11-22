import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
import os
from loader import Loader

LOADER = Loader()
def delete_item(table_name, dataSetGroupName, status):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    print(f"Status: {status}")

    try:
        get_response = table.query(KeyConditionExpression=Key('name').eq(dataSetGroupName))
        print(f"Items: {get_response['Items']}")
        if len(get_response['Items']) > 0:
            current_status = get_response['Items'][0].get("status")
            table.delete_item(
                Key={
                    'name': dataSetGroupName,
                    'status': current_status
                }
            )
            return "Deleted"
    except ClientError as e:
        print(f"Dynamo delete error: {e}")

    return "Nothing to delete"

def update_item(table_name, dataSetGroupName, status, datasetArn="None", eventTrackerId="None", campaignArn="None", trafficRatio="0", contextMap={}):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    print(f"Status: {status}")

    try:
        get_response = table.query(KeyConditionExpression=Key('name').eq(dataSetGroupName))
        current_status = get_response['Items'][0].get("status")
    except ClientError as e:
        print(f"Dynamo get current status error: {e}")
        current_status = ""

    try:
        response = table.update_item(
            Key={
                'name': dataSetGroupName,
                'status': status
            },
            UpdateExpression="set #S=:status_v, #eventTrackerId=:eventTrackerId, #datasetArn=:datasetArn, #campaignArn=:campaignArn, #trafficRatio=:trafficRatio, #context=:context",
            ExpressionAttributeNames={
                '#S': 'status',
                '#eventTrackerId': 'eventTrackerId',
                '#datasetArn': 'datasetArn',
                '#campaignArn': 'campaignArn',
                '#trafficRatio': 'trafficRatio',
                '#context': 'context',
            },
            ExpressionAttributeValues={
                ":status_v": status,
                ':eventTrackerId': eventTrackerId,
                ':datasetArn': datasetArn,
                ':campaignArn': campaignArn,
                ':context': contextMap,
                ':trafficRatio': trafficRatio
            },
            ReturnValues="UPDATED_NEW"
        )

        if current_status != status:
            delete_item(table_name, dataSetGroupName, current_status)

    except ClientError as e:
        print(f"Dynamo update error: {e}")

    return response



def lambda_handler(event, context):
    lambda_function_arn = context.invoked_function_arn
    aws_account_id = lambda_function_arn.split(":")[4]
    region = os.environ.get('AWS_REGION')

    print(f"Event: {event}" )


    if event.get('UpdateType') == "Delete":
        dataSetGroupName = event['datasetGroupArn'].split("dataset-group/")[1]
        response = delete_item(os.environ['SettingsTableName'], dataSetGroupName, "deleted")
        print(f"Dynamo reponse: {response}" )

    else:
        dataSetGroupName = event['datasetGroupName']
        datasetArn = f"arn:aws:personalize:${region}:${aws_account_id}:datasetArn/{event['datasetGroupName']}/ITEMS"

        campaignArn = f"arn:aws:personalize:${region}:${aws_account_id}:campaign/{event['campaignName']}"
        trafficRatio = event['trafficRatio']
        contextMap = {
            'default' : {
                'filter_name': dataSetName + '-unread'
            }
        }

        try:
            response = LOADER.personalize_cli.describe_event_tracker(
                eventTrackerArn=event['eventTrackerArn']
            )
            eventTrackerId = response['eventTrackers']['trackingId']
        except Exception as e:
            eventTrackerId = ""
            LOADER.logger.error(f'Error listing event trackers {e}')


        for filter in event['filters']:
            context = filter.get('context', 'none')
            contextMap[context] = {}
            contextMap[context]['filter_name'] = filter['name']
            contextMap[context]['filter_values'] = filter.get('filter_values', [])

        update_item(os.environ['SettingsTableName'], dataSetGroupName, "active", datasetArn, eventTrackerId, campaignArn, trafficRatio, contextMap)

    return
