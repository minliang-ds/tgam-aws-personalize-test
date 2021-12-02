from os import environ
import actions
from loader import Loader
import ssm_parameters

LOADER = Loader()

def lambda_handler(event, context):
    listETResponse = LOADER.personalize_cli.list_event_trackers(
        datasetGroupArn=event['datasetGroupArn'])
    if(len(listETResponse['eventTrackers']) > 0):
        eventTrackerArn = listETResponse['eventTrackers'][0]['eventTrackerArn']
        status = LOADER.personalize_cli.describe_event_tracker(
            eventTrackerArn=eventTrackerArn
        )['eventTracker']
        status = LOADER.personalize_cli.describe_event_tracker(
            eventTrackerArn=eventTrackerArn
        )['eventTracker']
    else:
        LOADER.logger.info(
            'Event tracker not found!'
        )
        datasetGroupArn = event['datasetGroupArn']
        eventTrackerName = event['datasetGroupName'] + '-' + event['eventTracker']['name']
        createStatus = LOADER.personalize_cli.create_event_tracker(
            name = eventTrackerName,
            datasetGroupArn = datasetGroupArn
        )
        eventTrackerArn = createStatus['eventTrackerArn']
        status = LOADER.personalize_cli.describe_event_tracker(
            eventTrackerArn=eventTrackerArn
        )['eventTracker']

    try:
        ssm_parameters.put_parameter("eventTrackerArn", eventTrackerArn)
        ssm_parameters.put_parameter("eventTrackerId", status['trackingId'])
    except:
        pass


    actions.take_action(status['status'])
    return eventTrackerArn