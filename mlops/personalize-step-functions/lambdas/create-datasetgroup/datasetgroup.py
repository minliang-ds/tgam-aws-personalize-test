from os import environ
import actions
from loader import Loader
import ssm_parameters
import re


ARN = 'arn:aws:personalize:{region}:{account}:dataset-group/{name}'
LOADER = Loader()


def lambda_handler(event, context):

    root = event['datasetGroup']['name']
    l = len(root)

    response = LOADER.personalize_cli.list_dataset_groups()

    datasetGroupNames = []
    for datasetgroup in response['datasetGroups']:
        if datasetgroup['name'].startswith(root):
            datasetGroupNames.append(datasetgroup['name'])
    
    if len(datasetGroupNames) == 0:
        datasetGroupArn = ARN.format(
            account=LOADER.account_id,
            name=event['datasetGroup']['name'] + '1',
            region=environ['AWS_REGION']
        )
    else:
        try:
            versions = []
            for datasetGroupName in datasetGroupNames:
                versions.append(int(datasetGroupName[l:]))
            datasetGroupArn = ARN.format(
                account=LOADER.account_id,
                name=event['datasetGroup']['name'] + str(max(versions) + 1),
                region=environ['AWS_REGION']
            )
        except Exception as e:
            LOADER.logger.error(f'Unexpected dataset group name {e}')
            raise e

    try:
        status = LOADER.personalize_cli.describe_dataset_group(
            datasetGroupArn=datasetGroupArn
        )['datasetGroup']

    except LOADER.personalize_cli.exceptions.ResourceNotFoundException:
        LOADER.logger.info(
            'Dataset Group not found! Will follow to create Dataset Group.'
        )
        LOADER.personalize_cli.create_dataset_group(**event['datasetGroup'])
        status = LOADER.personalize_cli.describe_dataset_group(
            datasetGroupArn=datasetGroupArn
        )['datasetGroup']

    ssm_parameters.put_parameter("datasetGroupName", event['datasetGroup']['name'])

    actions.take_action(status['status'])
    return datasetGroupArn
