from os import environ
from loader import Loader

ARN = 'arn:aws:personalize:{region}:{account}:campaign/{name}'
LOADER = Loader()


def lambda_handler(event, context):
    campaignArn = ARN.format(
        region=environ['AWS_REGION'],
        account=LOADER.account_id,
        name=event['name']+'Campaign'
    )
    solutionVersionArn = event['solutionVersionArn']

    update_campaign_response = LOADER.personalize_cli.update_campaign(
        campaignArn = campaignArn,
        solutionVersionArn = solutionVersionArn,
        minProvisionedTPS = 10,
    )

    return campaignArn