"""
inputs
@userId - required, string
@numResults - optional, int, max: 500, default: 25
@filterName - optional, string, default: unread

"""

from boto3 import client
personalize_cli = client('personalize-runtime')
dynamodb = client('dynamodb')

from boto3.dynamodb.types import TypeDeserializer
deserializer = TypeDeserializer()


from botocore.exceptions import ClientError

import json
import os
import decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)
        
region = os.environ['AWS_REGION']
account_id = os.environ['CurretnAccountId']
filter_prefix = os.environ['FiltersPrefix']
table_name = os.environ['DynamoDbTableName']

#		"widget_id": "recommended-art_same_section_mostpopular",
#		"include_read": false,
#		"include_content_types": "wire,news,blog,column,review,gallery",
#		"limit": 6,
#		"context": "art_same_section_mostpopular",
#		"width": "w620",
#		"include_sections": "canada",
#		"min_content_age": 61,
#		"platform": "desktop",
#		"max_content_age": 345601,
#		"rank": 1,
#		"last_content_ids": "4LTZGA2T7FA5FC3XJXTHCUGXLI",
#		"newsletter_ids": "",
#		"section": "/canada/",
#		"seo_keywords": "",
#		"visitor_type": "anonymous"


def handler(event, context):
    print(f"Event = {event}")
    body = json.loads(event['body'])
    payload = body.get("sub_requests")[0]

    reply = {}
    reply['recommendations'] = []
    reply["request_id"] = event.get("requestContext").get("requestId")
    reply["container_position"] = 0

    reply["widget_id"] = payload.get("widget_id")
    
    try:
        payload["limit"] = int(payload.get("limit"))
    except:
        payload["limit"] = 25
  
    try:
        arguments={
            'campaignArn': os.environ['CAMPAIGN_ARN'],
            'userId'     : body.get("visitor_id"),
            'numResults' : payload.get("limit"),
            'filterValues' : {}
        }
        
        #input validation
        if arguments["numResults"] > 500:
            arguments["numResults"] = 500
            
        #Add one to limit in case when personalize will return last_content_ids in reply
        #arguments["numResults"] += 1
        
        if payload.get("filterName"):
            arguments["filterArn"] =  f'arn:aws:personalize:{region}:{account_id}:filter/{filter_prefix}-{payload.get("filterName")}'
        else:
            arguments["filterArn"] = f'arn:aws:personalize:{region}:{account_id}:filter/{filter_prefix}-unread'

#        #if payload.get("last_content_ids"):
#        #    arguments["last_content_ids"] = payload.get("last_content_ids");
            
        #if payload.get("context"):
        #    arguments["filterValues"]["context"] = payload.get("context");
            
        #if payload.get("category"):
        #    arguments["filterValues"]["category"] = f'\"{payload.get("category")}\"';

        #print(f"RequestRecommendations = {arguments}")
        response = personalize_cli.get_recommendations(**arguments)
            
        #print(f"RawRecommendations = {response['itemList']}")
        reply['recommendations_debug'] = response['itemList']
        reply['recommendationId'] = response['recommendationId']
        
        #UpdatedDate => updated_at
        #promo_image - not sure how it converted
        #Section => section_meta_title and some convertion
        #caption ??
        #video_duration ??
        #author_rel ??
        #State ?
        #CanonicalURL => url
        #CreditLine > credit and some convertion
        #Sponsored ?? 
        #ContentId => content_id
        #ContentType => content_type
        #ContentRestriction => protection_product
        #PublishedDate => published_at
        #WordCount => word_count
        #byline = what if we have 2 ?
        
        try:
            response = dynamodb.batch_get_item(
                RequestItems={
                    table_name: {
                        'Keys': [{'ContentId': {'S': item["itemId"]}} for item in response['itemList']],
                        'AttributesToGet': [ 'Title', 'Deck', 'Byline', 'Category', 'Section', 'Keywords', 'State', 'CanonicalURL', 'CreditLine', 'Ownership', 'Sponsored', 'ContentId', 'ContentType', 'ContentRestriction', 'PublishedDate', 'WordCount', 'picture_rel', 'author_rel', 'video_duration', 'caption', 'promo_image', 'UpdatedDate']
                    }
                },
                ReturnConsumedCapacity='TOTAL'
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            item = response['Responses'].get(table_name)
            deserialized_item = [{k.lower(): deserializer.deserialize(v) for k, v in element.items()} for element in item]
            #
            #serialized_item = [{k: [v2 for k2, v2 in v.items()][0] for k, v in element.items()} for element in item]
            
            reply["recommendations"] = deserialized_item
            #reply["recommendations_debug"] = deserialized_item
            #print("BatchGetItem succeeded:")
            print(deserialized_item)
            
        return {'statusCode': '200', 'body': json.dumps([reply], cls=DecimalEncoder)}
    except personalize_cli.exceptions.ResourceNotFoundException as e:
        print(f"Personalize Error: {e}")
        return {'statusCode': '500', 'body': json.dumps("Campaign Not Found")}
    except personalize_cli.exceptions.InvalidInputException as e:
        print(f"Invalid Input Error: {e}")
        return {'statusCode': '400', 'body': json.dumps("Invalid Input")}
    except KeyError as e:
        print(f"Key Error: {e}")
        return {'statusCode': '400', 'body': json.dumps("Key Error")}
