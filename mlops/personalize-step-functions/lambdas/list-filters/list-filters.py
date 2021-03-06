from os import environ
from loader import Loader
import actions
import json

LOADER = Loader()


def lambda_handler(event, context):
    try:
        response = LOADER.personalize_cli.list_filters(
            datasetGroupArn=event['datasetGroupArn'],
            maxResults = 100
        )

        return json.loads(json.dumps(response['Filters'], default=str))
    except Exception as e:
        LOADER.logger.error(f'Error listing filters {e}')
        raise e
