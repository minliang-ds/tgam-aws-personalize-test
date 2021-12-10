from os import environ
from loader import Loader
import actions
from boto3 import client

LOADER = Loader()

STEP_FUNCTIONS_CLI = client('stepfunctions')

def lambda_handler(event, context):
    response = STEP_FUNCTIONS_CLI.describe_execution(
        executionArn = event['executionArn']
    )
    status = response['status']
    
    actions.take_action(status)
    return status