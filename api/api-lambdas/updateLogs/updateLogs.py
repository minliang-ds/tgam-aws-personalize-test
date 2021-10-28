import json
import boto3
import cfnresponse
from botocore.exceptions import ClientError

client = boto3.client('logs')

def handler(event, context):
    try:
        responseData = {}
        responseData['Data'] = "OK"

        print(f"Event: {event}")
        ContentLambdaName = event['ResourceProperties'].get('ContentLambdaName')
        RecommendationsLambdaName = event['ResourceProperties'].get('RecommendationsLambdaName')
        EventsLambdaName = event['ResourceProperties'].get('EventsLambdaName')
        ContentLogsRetention = event['ResourceProperties'].get('ContentLogsRetention')
        RecommendationsLogsRetention = event['ResourceProperties'].get('RecommendationsLogsRetention')
        EventsLogsRetention = event['ResourceProperties'].get('EventsLogsRetention')
    except:
        pass
    else:
        try:
            client.create_log_group(
                logGroupName=f"/aws/lambda/{ContentLambdaName}",
            )
        except:
            pass

        try:
            client.create_log_group(
                logGroupName=f"/aws/lambda/{RecommendationsLambdaName}",
            )
        except:
            pass

        try:
            client.create_log_group(
                logGroupName=f"/aws/lambda/{EventsLambdaName}",
            )
        except:
            pass

        try:
            client.put_retention_policy(
                logGroupName=f"/aws/lambda/{ContentLambdaName}",
                retentionInDays=int(ContentLogsRetention)
            )
            client.put_retention_policy(
                logGroupName=f"/aws/lambda/{RecommendationsLambdaName}",
                retentionInDays=int(RecommendationsLogsRetention)
            )

            client.put_retention_policy(
                logGroupName=f"/aws/lambda/{EventsLambdaName}",
                retentionInDays=int(EventsLogsRetention)
            )

        except ClientError as e:
            responseData = {}
            responseData['Data'] = f"{e}"


    cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData, "CustomResourcePhysicalID")