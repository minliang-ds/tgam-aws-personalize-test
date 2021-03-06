from os import environ
import actions
from loader import Loader
import time
import datetime

LOADER = Loader()
ARN = 'arn:aws:personalize:{region}:{account}:filter/{filter_name}'

def create_filter(dataset_group_arn, filter_expression, filter_name):

    filterARN = ARN.format(
        region=environ['AWS_REGION'],
        account=LOADER.account_id,
        filter_name=filter_name
    )

    try:
        status = LOADER.personalize_cli.describe_filter(
            filterArn=filterARN
        )['filter']['status']

    except LOADER.personalize_cli.exceptions.ResourceNotFoundException:
        LOADER.logger.info(
            'Filter not found! Will follow to create a new filter.'
        )
        LOADER.personalize_cli.create_filter(
            datasetGroupArn = dataset_group_arn,
            filterExpression = filter_expression,
            name = filter_name
        )
        status = LOADER.personalize_cli.describe_filter(
            filterArn=filterARN
        )['filter']['status']

    while status in {'CREATE PENDING', 'CREATE IN_PROGRESS'}:
        status = LOADER.personalize_cli.describe_filter(
            filterArn=filterARN
        )['filter']['status']
        time.sleep(1)  # Spacing out API calls to avoid ThrottlingExceptions

    if status != 'ACTIVE':
        raise actions.ResourceFailed

    return filterARN

def lambda_handler(event, context):
    filter_arns = []

    yesterday = datetime.date.today() - datetime.timedelta(1)
    ageLimit = datetime.date.today() - datetime.timedelta(3)
    ageFilterExpression = " | EXCLUDE ItemID WHERE Items.CREATION_TIMESTAMP < " + str(ageLimit.strftime("%s"))
    suffix = yesterday.strftime("%Y-%m-%d")

    for filter in event['filters']:
        filter_arn = create_filter(
            event['datasetGroupArn'],
            filter['filterExpression'],
            event['datasetGroupName'] + '-' + filter['name']
        )
        filter_arns.append(filter_arn)

        time.sleep(1)  # Spacing out API calls to avoid ThrottlingExceptions

        filter_arn = create_filter(
            event['datasetGroupArn'],
            filter['filterExpression'] + ageFilterExpression,
            event['datasetGroupName'] + '-' + filter['name'] + '-' + suffix
        )
        filter_arns.append(filter_arn)

        time.sleep(1)  # Spacing out API calls to avoid ThrottlingExceptions

    return filter_arns
