import logging
from boto3 import client


class Loader:
    def __init__(self):
        self.ssm_cli = client('ssm')
        self.personalize_cli = client('personalize')
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.account_id = client('sts').get_caller_identity()['Account']
