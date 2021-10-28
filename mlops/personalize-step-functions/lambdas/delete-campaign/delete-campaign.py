from os import environ
from loader import Loader
import actions
import ssm_parameters

LOADER = Loader()


def lambda_handler(event, context):
    try:
        response = LOADER.personalize_cli.delete_campaign(
            campaignArn=event['campaignArn']
        )

        ssm_parameters.delete_parameter("campaignArn")
        ssm_parameters.delete_parameter("campaignName")
        ssm_parameters.delete_parameter("minProvisionedTPS")
    except Exception as e:
        LOADER.logger.error(f'Error deleting campaign: {e}')
        raise e
