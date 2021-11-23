from os import environ
from loader import Loader
import json

ARN = 'arn:aws:personalize:{region}:{account}:dataset-group/{name}'
LOADER = Loader()


def lambda_handler(event, context):
    response = LOADER.personalize_cli.list_dataset_groups()

    root = event['datasetGroupName']
    l = len(root)

    datasetGroupNames = []
    for datasetgroup in response['datasetGroups']:
        if datasetgroup['name'].startswith(root):
            datasetGroupNames.append(datasetgroup['name'])

    toBeDeleted = []
    if len(datasetGroupNames) > 1:
        try:
            versions = []
            for datasetGroupName in datasetGroupNames:
                versions.append(int(datasetGroupName[l:]))
            m = max(versions)
            for version in versions:
                if version < m:
                    toBeDeleted.append({'datasetGroupArn': ARN.format(
                                            account=LOADER.account_id,
                                            name=event['datasetGroup']['name'] + str(version),
                                            region=environ['AWS_REGION']
                    )})
            return toBeDeleted
        except Exception as e:
            LOADER.logger.error(f'Unexpected dataset group name format {e}')
            raise e