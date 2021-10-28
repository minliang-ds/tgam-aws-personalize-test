from boto3 import client
from os import environ
from botocore.exceptions import ClientError
from loader import Loader

SHARED_LOADER = Loader()

def put_parameter(parameter_name, value):
    ssm_client = client('ssm')
    prefix_name=environ.get('ResourcesPrefix', 'tgam-personalize')
    env_name=environ.get('Environment', "dev")
    try:
        ssm_client.put_parameter(
            Name=f"/personalize/{prefix_name}/{env_name}/{parameter_name}",
            Description=f"Parameter {parameter_name} for: {prefix_name} env: {env_name}",
            Value=value,
            Type='String',
            Overwrite=True,
            Tier='Standard',
            DataType='text'
        )
    except ClientError as e:
        SHARED_LOADER.logger.error(
            f"put_parameter error: {e}"
        )



def delete_parameter(parameter_name):
    ssm_client = client('ssm')
    prefix_name=environ.get('ResourcesPrefix', 'tgam-personalize')
    env_name=environ.get('Environment', "dev")
    try:
        ssm_client.delete_parameter(
            Name=f"/personalize/{prefix_name}/{env_name}/{parameter_name}",
            )

    except ClientError as e:
        SHARED_LOADER.logger.error(
            f"delete_parameter error: {e}"
        )


