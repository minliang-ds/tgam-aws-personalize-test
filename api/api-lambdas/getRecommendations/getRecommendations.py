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
import time 

from boto3 import client
personalize_cli = client('personalize-runtime')
dynamodb = client('dynamodb')

from boto3.dynamodb.types import TypeDeserializer
deserializer = TypeDeserializer()

from botocore.exceptions import ClientError
from aws_embedded_metrics import metric_scope

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
        
region            = os.environ['AWS_REGION']
account_id        = os.environ['CurretnAccountId']
filter_prefix     = os.environ['FiltersPrefix']
sophi3_table_name = os.environ['Sophi3DynamoDbTableName']
sophi2_table_name = os.environ['Sophi2DynamoDbTableName']

attributes_to_get_sophi3 = [ 'Title', 'Deck', 'Byline', 'Category', 'Section', 'Keywords', 'State', 'CanonicalURL', 'CreditLine', 'Ownership', 'Sponsored', 'ContentId', 'ContentType', 'ContentRestriction', 'PublishedDate', 'WordCount', 'Caption', 'UpdatedDate']
attributes_to_get_sophi2 = ['ContentID', 'StoryRel', 'AuthorRel', 'PictureRel'];
sort_key_name_sophi3     = "ContentId"
sort_key_name_sophi2     = "ContentID"


def get_dynamo_data(dynamo_table, sort_key_name, attributes, item_list, return_type_map=False, return_type_list=False):
    if (len(item_list) > 0):
        try:
            deserialized_item = []
            processed_items = 0

            #if request ask for more then 100 items we need to split it
            #as batch_get_items can support only 100 items per request
            while processed_items < len(item_list):
                print(f"Debug processed_items: {processed_items} len {len(item_list)}")
        
                if ((len(item_list) - processed_items)  > 100):
                    items_limit = 100
                else:
                    items_limit = len(item_list) - processed_items
                    
                request_batch = [{sort_key_name: {'S': item["itemId"]}} for item in item_list[processed_items:processed_items+items_limit]]
                
                while request_batch:
                    db_response = dynamodb.batch_get_item(
                        RequestItems={
                            dynamo_table: {
                                'Keys':request_batch,
                                'AttributesToGet': attributes
                            }
                        },
                        ReturnConsumedCapacity='TOTAL'
                    )
                    items = db_response['Responses'].get(dynamo_table)
                    deserialized_iteration= [{k.lower(): deserializer.deserialize(v) for k, v in element.items()} for element in items]
                    
                    deserialized_item.extend(deserialized_iteration)
                    request_batch = db_response.get("UnprocessedKeys",  None)
                
                processed_items += items_limit
                
        except ClientError as e:
            print(f"Key Error: {e}")

        else:
            print(f"RawDynamoReply = {db_response}")


        if return_type_map:
            return_map = {element['contentid']: element for element in deserialized_item}
            return return_map;
        
        if return_type_list:
            return deserialized_item;

@metric_scope        
def handler(event, context, metrics):
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
        if arguments["numResults"] > 500:
            arguments["numResults"] = 500
            
        if payload.get("context") == "art_same_section_mostpopular":
            arguments["filterArn"] =  f'arn:aws:personalize:{region}:{account_id}:filter/{filter_prefix}-category'
            
            #section can be /canada/ or /canada/alberta/
            #in both cases we need category to be "canada"
            category = payload.get("section").split("/")
            if len(category) > 0:
                category = category[1]
            else:
                category = payload.get("section")
            
            arguments["filterValues"]["category"] = f'\"{category}\"';
        else:
            arguments["filterArn"] = f'arn:aws:personalize:{region}:{account_id}:filter/{filter_prefix}-unread'

        if payload.get("platform"):
            arguments["context"]['device_detector_visitorplatform'] = payload.get("platform").lower().capitalize();
            #capitalize as in model we have Mobile/Destop and its case sensitive

        if payload.get("visitor_type"):
            arguments["context"]['visitor_type'] = payload.get("visitor_type").lower().capitalize();
            #capitalize as in model we have Anonymous and its case sensitive


        print(f"RequestRecommendations = {arguments}")
        before_request = time.time_ns()
        response = personalize_cli.get_recommendations(**arguments)
        after_request = time.time_ns()

        metrics.put_metric("PersonalizeRequestTime", (int(after_request-before_request)/1000000), "Milliseconds")
        print(f"RawRecommendations = {response['itemList']}")
        
        #reply['recommendations_debug'] = response['itemList']
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
        
        
        
        #Mapping convertion fields from dynamo table to reply
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
                before_request = time.time_ns()
                deserialized_item = get_dynamo_data(sophi3_table_name, sort_key_name_sophi3, attributes_to_get_sophi3, response['itemList'], False, True)
                after_request = time.time_ns()
                metrics.put_metric("DynamoSophi2ReuqestTime", (int(after_request-before_request)/1000000), "Milliseconds")
                
                before_request = time.time_ns()
                images_map = get_dynamo_data(sophi2_table_name, sort_key_name_sophi2, attributes_to_get_sophi2, response['itemList'], True, False)
                after_request = time.time_ns()
                metrics.put_metric("DynamoSophi3ReuqestTime", (int(after_request-before_request)/1000000), "Milliseconds")
                
                #print(f"Images map: {images_map}")
                #print(f"Recommendation list: {deserialized_item}")
                

        except ClientError as e:
            print(f"Key Error: {e}")

        else:
            if (len(deserialized_item) > 0):
                reply["recommendations"] = []

                for row in deserialized_item:

                  #Updaete formating of keys to match reply requirements
                  for k, v in names_key.items():
                    for old_name in list(row):
                      if k == old_name:
                        row[v] = row.pop(old_name)
                    
                  #byline in Dynamo is list of strings (sometimes empty) and we need to return it as string
                  if row.get('byline') and (type(row.get('byline')) is list):
                    if len(row['byline']) > 0:
                        row['byline'] = ' and '.join(row['byline'])
                    else:
                        row['byline'] = ''
            
                  #Exlude last_content_ids from result 
                  current_content_id = row.get('content_id')
                  if payload.get("last_content_ids") and current_content_id == payload.get("last_content_ids"):
                    continue;
                    
                  #Merging information about images from sophi2 table
                  if images_map.get(current_content_id):
                      row['author_rel'] = [{}]
                      if images_map[current_content_id].get('authorrel') and len(images_map[current_content_id].get('authorrel')) > 0:
                          row['author_rel'][0]['url220'] = images_map[current_content_id].get('authorrel')[0].get('url220', "")

                      row['picture_rel'] = [{}]
                      if images_map[current_content_id].get('picturerel') and len(images_map[current_content_id].get('picturerel')) > 0:
                        row['picture_rel'][0]['url220'] = images_map[current_content_id].get('picturerel')[0].get('url220', "")

                      #copy formatted from arc_content.PictureRel
                      row['promo_image'] = {}
                      row['promo_image']['urls'] = {}
                      if images_map[current_content_id].get('picturerel') and len(images_map[current_content_id].get('picturerel')) > 0:
                        row['promo_image']['urls']['url220'] = images_map[current_content_id].get('picturerel')[0].get('url220', "")

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
