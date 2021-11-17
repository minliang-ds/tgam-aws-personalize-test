import time
import json
import os
import decimal

from boto3 import client
from boto3.session import Session
from boto3.dynamodb.types import TypeDeserializer

from botocore import config as boto_config
from botocore.credentials import RefreshableCredentials
from botocore.session import get_session
from botocore.exceptions import ClientError
from aws_embedded_metrics import metric_scope
from datetime import date, timedelta

def _refresh():
    sts_client = client('sts')
    print(f"Refresh tokens by calling assume_role again")

    params = {
        "RoleArn": os.environ.get('CrossAccountSophi2Role'),
        "RoleSessionName": "CrossAccountSophi2Role",
        "DurationSeconds": 3600,
    }

    response = sts_client.assume_role(**params).get("Credentials")
    credentials = {
        "access_key": response.get("AccessKeyId"),
        "secret_key": response.get("SecretAccessKey"),
        "token": response.get("SessionToken"),
        "expiry_time": response.get("Expiration").isoformat(),
    }
    return credentials

def get_dynamo_data(dynamo_client, dynamo_table, sort_key_name, attributes, item_list, return_type_map=False, return_type_list=False, api_gateway_request_id="NONE"):
    if (len(item_list) > 0):
        try:
            deserialized_item = []
            processed_items = 0

            #if request ask for more then 100 items we need to split it
            #as batch_get_items can support only 100 items per request
            while processed_items < len(item_list):
                if ((len(item_list) - processed_items)  > 100):
                    items_limit = 100
                else:
                    items_limit = len(item_list) - processed_items

                request_batch = [{sort_key_name: {'S': item["itemId"]}} for item in item_list[processed_items:processed_items+items_limit]]

                while request_batch:
                    db_response = dynamo_client.batch_get_item(
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
            print(f"RequestID: {api_gateway_request_id} Key Error: {e}")

        if return_type_map:
            return_map = {element['contentid']: element for element in deserialized_item}
            return return_map;

        if return_type_list:
            return deserialized_item;

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

region            = os.environ.get('AWS_REGION')
account_id        = os.environ.get('CurrentAccountId')
filter_prefix     = os.environ.get('FiltersPrefix')
sophi2_role_arn   = os.environ.get('CrossAccountSophi2Role')
enviroment        = os.environ.get('Environment')

deserializer      = TypeDeserializer()
config = boto_config.Config(
    connect_timeout=1, read_timeout=1,
    retries={'max_attempts': 2})

personalize_cli = client('personalize-runtime', config=config)
client_sophi3 = client('dynamodb', config=config)

if sophi2_role_arn and "arn" in sophi2_role_arn:
    session_credentials = RefreshableCredentials.create_from_metadata(
        metadata=_refresh(),
        refresh_using=_refresh,
        method="sts-assume-role",
    )
    sts_session = get_session()
    sts_session._credentials = session_credentials
    autorefresh_session = Session(botocore_session=sts_session)
    client_sophi2 = autorefresh_session.client("dynamodb", config=config)
else:
    client_sophi2 = client('dynamodb', config=config)

attributes_to_get_sophi3 = [
    'Title',
    'Deck',
    'Byline',
    'Category',
    'Section',
    'Keywords',
    'State',
    'CanonicalURL',
    'CreditLine',
    'Ownership',
    'Sponsored',
    'ContentId',
    'ContentType',
    'ContentRestriction',
    'PublishedDate',
    'WordCount',
    'Caption',
    'UpdatedDate',
    'Label'
]

attributes_to_get_sophi2 = [
    'ContentID',
    'StoryRel',
    'AuthorRel',
    'PictureRel'
]

sort_key_name_sophi3 = "ContentId"
sort_key_name_sophi2 = "ContentID"

#Mapping conversion fields from dynamo table to reply
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
    'Label'.lower()                : 'label'
}

return_headers = {
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Origin':  '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST'
}

category_mapping = {
    "technology":           "business",
    "globe-investor":       "investing",
    "news":                 "canada",
    "globe-drive":          "drive",
    "report-on-business":   "business"
}

@metric_scope
def handler(event, context, metrics):
    api_gateway_request_id = event.get("requestContext").get("requestId")
    print(f"RequestID: {api_gateway_request_id} Event = {event}")
    metrics.set_property("ApiRequestId", api_gateway_request_id)
    metrics.set_property("LambdaRequestId", context.aws_request_id)

    body = json.loads(event['body'])
    payload = body.get("sub_requests")[0]

    try:
        if event.get('multiValueHeaders').get('origin')[0].endswith("theglobeandmail.com"):
            return_headers['Access-Control-Allow-Origin'] = event.get('multiValueHeaders').get('origin')[0]
    except:
        #no pass as security scanner will complain More Info: https://bandit.readthedocs.io/en/latest/plugins/b110_try_except_pass.html
        return_headers['Access-Control-Allow-Origin'] = '*'

    deserialized_item = []

    reply = {}
    reply['recommendations'] = []
    reply["request_id"] = api_gateway_request_id
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
            filter_base =  f'arn:aws:personalize:{region}:{account_id}:filter/{filter_prefix}-category'

            #section can be /canada/ or /canada/alberta/
            #in both cases we need category to be "canada"
            if payload.get("include_sections"):
                category = payload.get("include_sections")
            elif payload.get("section"):
                category = payload.get("section").split("/")
                if len(category) > 0:
                    category = category[1]
                else:
                    category = payload.get("section")

            if category_mapping.get(category):
                category = category_mapping.get(category)

            arguments["filterValues"]["category"] = f'\"{category}\"';
        else:
            filter_base = f'arn:aws:personalize:{region}:{account_id}:filter/{filter_prefix}-unread'

        if payload.get("platform"):
            arguments["context"]['device_detector_visitorplatform'] = payload.get("platform").lower().capitalize();
            #capitalize as in model we have Mobile/Destop and its case sensitive

        if payload.get("visitor_type"):
            arguments["context"]['visitor_type'] = payload.get("visitor_type").lower().capitalize();
            #capitalize as in model we have Anonymous and its case sensitive


        print(f"RequestID: {api_gateway_request_id} RequestRecommendations = {arguments}")
        before_request = time.time_ns()

        try:
            filter_date_prefix = date.today() - timedelta(days=1)
            arguments["filterArn"] = f'{filter_base}-{filter_date_prefix.strftime("%Y-%m-%d")}'
            response = personalize_cli.get_recommendations(**arguments)
        except personalize_cli.exceptions.InvalidInputException:
            #default to filter without date if filters with date do not exist
            arguments["filterArn"] = filter_base
            metrics.set_property("personalizeFilter", arguments["filterArn"])
            response = personalize_cli.get_recommendations(**arguments)

        metrics.set_property("personalizeFilter", arguments["filterArn"])
        after_request = time.time_ns()

        metrics.put_metric("PersonalizeRequestTime", (int(after_request-before_request)/1000000), "Milliseconds")

        #print(f"RequestID: {api_gateway_request_id} RawRecommendations = {response['itemList']}")

        metrics.put_metric("ReturnRecommendations", (len(response['itemList'])), "None")
        metrics.put_metric("MissingRecommendations", (arguments["numResults"] - len(response['itemList'])), "None")

        #reply['recommendations_debug'] = response['itemList']
        reply['recommendationId'] = response['recommendationId']

        try:
            if (len(response.get('itemList', [])) > 0):
                before_request = time.time_ns()
                deserialized_item = get_dynamo_data(client_sophi3, os.environ.get('Sophi3DynamoDbTableName'), sort_key_name_sophi3, attributes_to_get_sophi3, response['itemList'], False, True, api_gateway_request_id)
                after_request = time.time_ns()
                metrics.put_metric("DynamoSophi2RequestTime", (int(after_request-before_request)/1000000), "Milliseconds")
                metrics.put_metric("MissingDataDynamoSophi2", (arguments["numResults"] - len(deserialized_item)), "None")

                before_request = time.time_ns()
                images_map = get_dynamo_data(client_sophi2, os.environ.get('Sophi2DynamoDbTableName'), sort_key_name_sophi2, attributes_to_get_sophi2, response['itemList'], True, False, api_gateway_request_id)
                after_request = time.time_ns()
                metrics.put_metric("DynamoSophi3RequestTime", (int(after_request-before_request)/1000000), "Milliseconds")
                metrics.put_metric("MissingDataDynamoSophi3", (arguments["numResults"] - len(images_map)), "None")

        except ClientError as e:
            print(f"RequestID: {api_gateway_request_id} Key Error: {e}")

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
        return {'statusCode': '200', 'headers': return_headers, 'body': json.dumps([reply], cls=DecimalEncoder)}
    except personalize_cli.exceptions.ResourceNotFoundException as e:
        print(f"RequestID: {api_gateway_request_id} Personalize Error: {e}")
        return {'statusCode': '500', 'headers': return_headers, 'body': json.dumps("Campaign Not Found")}
    except personalize_cli.exceptions.InvalidInputException as e:
        print(f"RequestID: {api_gateway_request_id} Invalid Input Error: {e}")
        return {'statusCode': '400', 'headers': return_headers, 'body': json.dumps("Invalid Input")}
    except KeyError as e:
        print(f"RequestID: {api_gateway_request_id} Key Error: {e}")
        return {'statusCode': '400', 'headers': return_headers, 'body': json.dumps("Key Error")}
