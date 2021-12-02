from os import environ
from loader import Loader

ARN = 'arn:aws:personalize:{region}:{account}:solution/{name}'
LOADER = Loader()


def lambda_handler(event, context):
    solutionArn = ARN.format(
        region=environ['AWS_REGION'],
        account=LOADER.account_id,
        name=event['datasetGroupName'] + '-' + event['solutionName']
    )
    trainingMode = event['trainingMode']
    
    create_solution_version_response = LOADER.personalize_cli.create_solution_version(
        solutionArn = solutionArn,
        trainingMode = trainingMode
    )
    
    solutionVersionArn = create_solution_version_response['solutionVersionArn']

    return solutionVersionArn
