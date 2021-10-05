from boto3 import client
personalize_cli = client('personalize-runtime')
import json
import os

region = os.environ['AWS_REGION']
account_id = os.environ['CurretnAccountId']

def handler(event, context):
    print(f"Event = {event}")
    payload = json.loads(event['body'])
    try:
        #input validation
        if payload.get("numResults") and type(payload.get("numResults")) != int:
            payload["numResults"] = 25;
            
        elif payload.get("numResults") and type(payload.get("numResults")) > 500:
            payload["numResults"] = 500;
            
            
    
        response = personalize_cli.get_recommendations(
            campaignArn=os.environ['CAMPAIGN_ARN'],
            userId=payload['userId'],
            numResults = payload.get("numResults") ? payload.get("numResults") : 25,
            #filterArn = payload.get("filterName") ? f'arn:aws:personalize:{region}:{account_id}:filter/{payload.get("filterName")}' : f'arn:aws:personalize:{region}:{account_id}:filter/unread',
            # context=payload['context']
            )
        print(f"RawRecommendations = {response['itemList']}")
        return {'statusCode': '200', 'body': json.dumps(response)}
    except personalize_cli.exceptions.ResourceNotFoundException as e:
        print(f"Personalize Error: {e}")
        return {'statusCode': '500', 'body': json.dumps("Campaign Not Found")}
    except personalize_cli.exceptions.InvalidInputException as e:
        print(f"Invalid Input Error: {e}")
        return {'statusCode': '400', 'body': json.dumps("Invalid Input")}
    except KeyError as e:
        print(f"Key Error: {e}")
        return {'statusCode': '400', 'body': json.dumps("Key Error")}
