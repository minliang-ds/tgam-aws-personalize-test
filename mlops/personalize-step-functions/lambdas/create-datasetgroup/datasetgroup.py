from os import environ
import actions
from loader import Loader
import ssm_parameters


ARN = 'arn:aws:personalize:{region}:{account}:dataset-group/{name}'
LOADER = Loader()


def lambda_handler(event, context):

    root = event['datasetGroup']['name']
    l = len(root)

    response = LOADER.personalize_cli.list_dataset_groups()

    datasetGroupNames = []
    for datasetgroup in response['datasetGroups']:
        if datasetgroup['name'].startswith(root) and datasetgroup['name'][l:].isdigit():
            datasetGroupNames.append(datasetgroup['name'])
    
    try:
        versions = []
        for datasetGroupName in datasetGroupNames:
            suffix = datasetGroupName[l:]
            versions.append(int(suffix))
        newName = event['datasetGroup']['name'] + str(max(versions) + 1)
        datasetGroupArn = ARN.format(
            account=LOADER.account_id,
            name=newName,
            region=environ['AWS_REGION']
        )
    except:
        newName = event['datasetGroup']['name'] + '1'
        datasetGroupArn = ARN.format(
            account=LOADER.account_id,
            name=newName,
            region=environ['AWS_REGION']
        )

    try:
        status = LOADER.personalize_cli.describe_dataset_group(
            datasetGroupArn=datasetGroupArn
        )['datasetGroup']

    except LOADER.personalize_cli.exceptions.ResourceNotFoundException:
        LOADER.logger.info(
            'Dataset Group not found! Will follow to create Dataset Group.'
        )
        LOADER.personalize_cli.create_dataset_group(name=newName)
        status = LOADER.personalize_cli.describe_dataset_group(
            datasetGroupArn=datasetGroupArn
        )['datasetGroup']

    ssm_parameters.put_parameter("datasetGroupName", newName)

    datasetGroup = {}
    datasetGroup['datasetGroupArn'] = datasetGroupArn
    datasetGroup['name'] = newName
    return datasetGroup
