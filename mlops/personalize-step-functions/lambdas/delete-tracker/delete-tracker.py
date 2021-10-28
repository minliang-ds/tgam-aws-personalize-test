from os import environ
from loader import Loader
import actions
import ssm_parameters


LOADER = Loader()


def lambda_handler(event, context):
    status = LOADER.personalize_cli.delete_event_tracker(
        eventTrackerArn=event['eventTrackerArn']
    )
    ssm_parameters.delete_parameter("eventTrackerArn")
    ssm_parameters.delete_parameter("eventTrackerId")
