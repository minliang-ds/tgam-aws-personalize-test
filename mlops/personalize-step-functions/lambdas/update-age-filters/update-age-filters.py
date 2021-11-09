import actions
import datetime
import json
import time

from os import environ
from loader import Loader


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
        return None

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

    if status != 'ACTIVE':
        raise actions.ResourceFailed

    return filterARN

def delete_filter(filter_name):

    filterARN = ARN.format(
        region=environ['AWS_REGION'],
        account=LOADER.account_id,
        filter_name=filter_name
    )

    try:
        response = LOADER.personalize_cli.delete_filter(
            filterArn=filterARN
        )
        return filterARN
    except LOADER.personalize_cli.exceptions.ResourceNotFoundException:
        return None

def list_filters(datasetGroupArn):
    try:
        response = LOADER.personalize_cli.list_filters(
            datasetGroupArn=datasetGroupArn,
            maxResults = 100
        )

        return json.loads(json.dumps(response['Filters'], default=str))
    except Exception as e:
        LOADER.logger.error(f'Error listing filters {e}')
        raise e

def lambda_handler(event, context):
    yesterday = datetime.date.today() - datetime.timedelta(1)
    two_days_ago = datetime.date.today() - datetime.timedelta(2)
    three_days_ago = datetime.date.today() - datetime.timedelta(3)
    
    deleteFilterSuffix = three_days_ago.strftime("%Y-%m-%d")
    anchorFilterSuffix = two_days_ago.strftime("%Y-%m-%d")
    createFilterSuffix = yesterday.strftime("%Y-%m-%d")
    
    newTimeStamp = str(yesterday.strftime("%s"))
    
    datasetGroupArn = 'arn:aws:personalize:{region}:{account}:dataset-group/{prefix}'.format(
        region=environ['AWS_REGION'],
        account=LOADER.account_id,
        prefix=environ['ResourcesPrefix']
    )

    filters = list_filters(datasetGroupArn)

    createdFilters = []
    deletedFilters = []
    for filter in filters:
        if filter['name'][-10:] == anchorFilterSuffix:
            response = LOADER.personalize_cli.describe_filter(
                filterArn=filter['filterArn']
            )['filter']

            created_filter_arn = create_filter(
                datasetGroupArn,
                response['filterExpression'][:-10] + newTimeStamp,
                filter['name'][:-10] + createFilterSuffix
            )
            createdFilters.append(created_filter_arn)

            deleted_filter_arn = delete_filter(filter['name'][:-10] + deleteFilterSuffix)
            deletedFilters.append(deleted_filter_arn)

            time.sleep(10)  # Spacing out API calls to avoid ThrottlingExceptions

    return (createdFilters, deletedFilters)
