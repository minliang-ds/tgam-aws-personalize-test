from os import environ
from loader import Loader
import actions

LOADER = Loader()


def lambda_handler(event, context):
    campaignArn = event['campaignArn']
    describe_campaign_response = LOADER.personalize_cli.describe_campaign(
        campaignArn = campaignArn
    )
    status = describe_campaign_response['campaign']['latestCampaignUpdate']
    
    actions.take_action(status['status'])
    return status['status']