from os import environ
from loader import Loader
import actions

LOADER = Loader()


def lambda_handler(event, context):
    status = LOADER.personalize_cli.describe_dataset_group(
        datasetGroupArn=event['datasetGroupArn']
    )['datasetGroup']

    actions.take_action(status['status'])
    return status['status']