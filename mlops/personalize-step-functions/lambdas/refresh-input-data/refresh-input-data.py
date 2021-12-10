import boto3
import os

s3 = boto3.resource('s3')

def lambda_handler(event, context):
    SOURCE_BUCKET = os.environ['SourceBucketName']
    DEST_BUCKET = event['bucket']

    old_bucket = s3.Bucket(SOURCE_BUCKET)
    new_bucket = s3.Bucket(DEST_BUCKET)

    # Create Source Prefix, Destination Prefix Pairs
    datasets = [
        ('glue-job/Interactions/', 'Interactions/'),
        ('glue-job/Items/', 'Items/')
    ]

    for dataset in datasets:
        SOURCE_PREFIX = dataset[0]
        DEST_PREFIX = dataset[1]
        
        # Delete
        new_bucket.objects.filter(Prefix=DEST_PREFIX).delete()
        
        # Copy
        for obj in old_bucket.objects.filter(Prefix=SOURCE_PREFIX):
            old_source = {'Bucket': SOURCE_BUCKET,
                        'Key': obj.key}
            # replace the prefix
            new_key = obj.key.replace(SOURCE_PREFIX, DEST_PREFIX, 1)
            new_obj = new_bucket.Object(new_key)
            new_obj.copy(old_source)
