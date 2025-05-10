import boto3
from os import walk
from uuid import uuid4
from datetime import datetime
from createPresignedUrl import create_presigned_url

bucket = "postagram-bucket-ensai20250510222321853400000001"
table_name = "postagram"

s3 = boto3.resource("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(table_name)


with table.batch_writer() as batch:
    for dirpath, dirnames, filenames in walk("s3"):
        if filenames:
            user = dirpath.split("/")[1]

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
                    "id": "POST#" + post_id,
                    "body": "",
                    "title": "",
                }

                batch.put_item(Item=item)

                print(
                    f"Uploaded image {filename} for user {user} to S3 with post ID {post_id} and added metadata to DynamoDB."
                )
