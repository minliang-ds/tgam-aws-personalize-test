from os import environ
from loader import Loader
import actions


LOADER = Loader()


def lambda_handler(event, context):
    try:
        response = LOADER.personalize_cli.delete_filter(
            filterArn=event['filterArn']
        )
    except Exception as e:
        LOADER.logger.error(f'Error deleting filter: {e}')
        raise e
