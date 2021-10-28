from os import environ
from loader import Loader
import ssm_parameters

ARN = 'arn:aws:personalize:{region}:{account}:campaign/{name}'
LOADER = Loader()


def lambda_handler(event, context):
    campaignArn = ARN.format(
        region=environ['AWS_REGION'],
        account=LOADER.account_id,
        name=event['campaignName']
    )
    solutionVersionArn = event['solutionVersionArn']

    update_campaign_response = LOADER.personalize_cli.update_campaign(
        campaignArn = campaignArn,
        solutionVersionArn = solutionVersionArn,
        minProvisionedTPS = event['minProvisionedTPS'],
    )

    try:
        ssm_parameters.put_parameter("campaignArn", campaignArn)
        ssm_parameters.put_parameter("campaignName", event['campaignName'])
        ssm_parameters.put_parameter("minProvisionedTPS", event['minProvisionedTPS'])
    except:
        pass

    return campaignArn