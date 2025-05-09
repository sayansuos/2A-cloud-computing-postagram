import boto3
from os import walk
from uuid import uuid4
from datetime import datetime
from createPresignedUrl import create_presigned_url

# S3 and DynamoDB Setup
bucket = "postagram-bucket-ensai20250506165208853700000001"
table_name = "postagram"

# Initialize S3 and DynamoDB clients
s3 = boto3.resource("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(table_name)

# Path to the local folder with user data
local_folder = "s3"  # Replace with the path to your local folder

# Iterate through the directories and files
with table.batch_writer() as batch:
    for dirpath, dirnames, filenames in walk(local_folder):
        if filenames:  # Only process directories that contain files
            user = dirpath.split("/")[
                1
            ]  # Assuming the last part of the path is the user name

            for filename in filenames:
                post_id = dirpath.split("/")[2]

                # S3 file path (image storage format)
                s3_key = f"{user}/{post_id}/{filename}"

                # Upload the image to S3
                with open(f"{dirpath}/{filename}", "rb") as file:
                    s3.Object(bucket, s3_key).put(Body=file)

                # Construct metadata for DynamoDB (we're assuming body, label, and title might be added from your local data)
                item = {
                    "user": "USER#" + user,
                    "id": "POST#" + post_id,  # Use the unique post ID here
                    "body": "",  # This should be filled with actual content (if available)
                    "label": [],  # This should be filled with labels if available
                    "title": "",  # Assuming the title is the file name, change if needed
                    "path": s3_key,
                }

                # Add the metadata item to DynamoDB
                batch.put_item(Item=item)

                print(
                    f"Uploaded image {filename} for user {user} to S3 with post ID {post_id} and added metadata to DynamoDB."
                )
