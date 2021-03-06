from os import environ
import actions
from loader import Loader
import ssm_parameters

ARN = 'arn:aws:personalize:{region}:{account}:campaign/{name}'
LOADER = Loader()


def lambda_handler(event, context):
    campaignName = event['datasetGroupName'] + '-' + event['campaign']['name']
    campaignArn = ARN.format(
        region=environ['AWS_REGION'],
        account=LOADER.account_id,
        name=campaignName
    )
    try:
        status = LOADER.personalize_cli.describe_campaign(
            campaignArn=campaignArn
        )['campaign']
        try:
            ssm_parameters.put_parameter("campaignArn", campaignArn)
            ssm_parameters.put_parameter("campaignName", campaignName)
            ssm_parameters.put_parameter("minProvisionedTPS", str(event['campaign']['minProvisionedTPS']))
        except:
            pass
        # Point to new campaign if the new solution version is not the one listed in the campaign
        if(status['solutionVersionArn'] != event['solutionVersionArn']):
            try:
                newStatus = LOADER.personalize_cli.update_campaign(
                    campaignArn=campaignArn,
                    solutionVersionArn=event['solutionVersionArn'],
                    minProvisionedTPS=event['campaign']['minProvisionedTPS'])
                status = LOADER.personalize_cli.describe_campaign(
                        campaignArn=campaignArn
                    )['campaign']
                actions.take_action(status['latestCampaignUpdate']['status'])
                return campaignArn
            except LOADER.personalize_cli.exceptions.ResourceInUseException:
                actions.take_action(status['latestCampaignUpdate']['status'])
                return campaignArn

    except LOADER.personalize_cli.exceptions.ResourceNotFoundException:
        LOADER.logger.info(
            'Campaign not found! Will follow to create a new campaign.'
        )
        LOADER.personalize_cli.create_campaign(
            name=campaignName,
            solutionVersionArn=event['solutionVersionArn'],
            minProvisionedTPS=event['campaign']['minProvisionedTPS']
        )
        status = LOADER.personalize_cli.describe_campaign(
            campaignArn=campaignArn
        )['campaign']

    actions.take_action(status['status'])
    return campaignArn
