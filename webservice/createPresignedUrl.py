import logging
import boto3
from boto3.dynamodb.conditions import Key
import os
import json
import uuid
from pathlib import Path
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

bucket_name = os.getenv("BUCKET")


def create_presigned_url(object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client("s3")
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_name},
            ExpiresIn=expiration,
        )
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response
