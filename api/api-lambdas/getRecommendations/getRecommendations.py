"""
inputs
@visitor_id - required, string, userID for personalize
@sub_requests[0].limit - optional, int, max: 100, default: 25, limit of return recommendation
@sub_requests[0].context - optional, string, example: art_same_section_mostpopular, art_mostpopular, user_container_recommendations, mobile_art_morestories
@sub_requests[0].platform - optional, string user platform 
@sub_requests[0].visitor_type - optional, string user type 
@sub_requests[0].section - optional, string convert to filter example: 

{
  "sub_requests": [
    {
      "widget_id": "recommended-art_same_section_mostpopular",
      "include_read": false,
      "include_content_types": "wire,news,blog,column,review,gallery",
      "limit": 6,
      "context": "art_same_section_mostpopular",
      "width": "w620",
      "include_sections": "business",
      "min_content_age": 61,
      "platform": "desktop",
      "max_content_age": 345601,
      "rank": 1,
      "last_content_ids": "IBIPXDSTAVFNTMRN5FXZXJFKRI",
      "newsletter_ids": "",
      "section": "/business/",
      "seo_keywords": "",
      "visitor_type": "registered"
    }
  ],
  "platform": "desktop",
  "visitor_id": "82889d15-188b-41ae-bf20-33982546e7b5",
  "hash_id": ""
}
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
            'campaignArn'  : os.environ['CAMPAIGN_ARN'],
            'userId'       : body.get("visitor_id"),
            'numResults'   : payload.get("limit"),
            'filterValues' : {},
            'context'      : {}
        }
        
        #Add one to limit in case when personalize will return last_content_ids in reply
        arguments["numResults"] += 1

        #input validation
        if arguments["numResults"] > 100:
            arguments["numResults"] = 100
            
        if payload.get("context") == "art_same_section_mostpopular":
            arguments["filterArn"] =  f'arn:aws:personalize:{region}:{account_id}:filter/{filter_prefix}-category'
            arguments["filterValues"]["category"] = f'\"{payload.get("section").replace("/","")}\"';
        else:
            arguments["filterArn"] = f'arn:aws:personalize:{region}:{account_id}:filter/{filter_prefix}-unread'

        if payload.get("platform"):
            arguments["context"]['device_detector_visitorplatform'] = payload.get("platform").lower().capitalize();
            #capitalize as in model we have Mobile/Destop and its case sensitive

        if payload.get("visitor_type"):
            arguments["context"]['visitor_type'] = payload.get("visitor_type").lower().capitalize();
            #capitalize as in model we have Anonymous and its case sensitive


        print(f"RequestRecommendations = {arguments}")
        response = personalize_cli.get_recommendations(**arguments)
            
        print(f"RawRecommendations = {response['itemList']}")
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
        
        names_key = { 
          'WordCount'.lower()            : 'word_count' ,
          'ContentType'.lower()          : 'content_type' ,
          'PublishedDate'.lower()        : 'published_at', 
          'UpdatedDate'.lower()          : 'updated_at',
          'Section'.lower()              : 'section_meta_title',
          'CanonicalURL'.lower()         : 'url',
          'CreditLine'.lower()           : 'credit',
          'ContentId'.lower()            : 'content_id',
          'ContentType'.lower()          : 'content_type',
          'ContentRestriction'.lower()   : 'protection_product',
          'ContentType'.lower()          : 'content_type',
        }

        try:
            if (len(response['itemList']) > 0):
                db_response = dynamodb.batch_get_item(
                    RequestItems={
                        table_name: {
                            'Keys': [{'ContentId': {'S': item["itemId"]}} for item in response['itemList']],
                            'AttributesToGet': [ 'Title', 'Deck', 'Byline', 'Category', 'Section', 'Keywords', 'State', 'CanonicalURL', 'CreditLine', 'Ownership', 'Sponsored', 'ContentId', 'ContentType', 'ContentRestriction', 'PublishedDate', 'WordCount', 'picture_rel', 'author_rel', 'video_duration', 'caption', 'promo_image', 'UpdatedDate']
                        }
                    },
                    ReturnConsumedCapacity='TOTAL'
                )
        except ClientError as e:
            print(e.db_response['Error']['Message'])
        else:
            if (len(response['itemList']) > 0):
                reply["recommendations"] = []
                
                item = db_response['Responses'].get(table_name)
                deserialized_item = [{k.lower(): deserializer.deserialize(v) for k, v in element.items()} for element in item]
                
                for row in deserialized_item:
                  if payload.get("last_content_ids") and row.get('contentid') == payload.get("last_content_ids"):
                    continue;

                  for k, v in names_key.items():
                    for old_name in list(row):
                      if k == old_name:
                        row[v] = row.pop(old_name)
                    
                  reply["recommendations"].append(row)
                  
                reply["recommendations"] = reply["recommendations"][:arguments["numResults"] - 1] 
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
