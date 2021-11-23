from os import environ
from loader import Loader
import actions
from boto3 import client

LOADER = Loader()

STEP_FUNCTIONS_CLI = client('stepfunctions')

def lambda_handler(event, context):
    response = client.describe_execution(
        executionArn = event['output']['executionArn']
    )
    status = response['status']
    
    actions.take_action(status)
    return status