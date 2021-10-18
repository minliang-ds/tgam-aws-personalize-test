from os import environ
from loader import Loader
import actions
import json
LOADER = Loader()


def lambda_handler(event, context):
    try:
        response = LOADER.personalize_cli.list_campaigns(
            solutionArn=event['solutionArn'],
            maxResults=100
        )

        return json.loads(json.dumps(response['campaigns'], default=str))
    except Exception as e:
        LOADER.logger.error(f'Error listing campaigns {e}')
        raise e
