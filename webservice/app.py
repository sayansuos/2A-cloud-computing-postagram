#################################################################################################
##                                                                                             ##
##                                 NE PAS TOUCHER CETTE PARTIE                                 ##
##                                                                                             ##
## 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 ##
import boto3
from botocore.config import Config
import os
import uuid
from dotenv import load_dotenv
from typing import Union
import logging
from fastapi import FastAPI, Request, status, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from getSignedUrl import getSignedUrl

load_dotenv()

app = FastAPI()
logger = logging.getLogger("uvicorn")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logger.error(f"{request}: {exc_str}")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


class Post(BaseModel):
    title: str
    body: str


my_config = Config(
    region_name="us-east-1",
    signature_version="v4",
)

dynamodb = boto3.resource("dynamodb", config=my_config)
table = dynamodb.Table(os.getenv("DYNAMO_TABLE"))
s3_client = boto3.client(
    "s3", config=boto3.session.Config(signature_version="s3v4")
)
bucket = os.getenv("BUCKET")

## ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ##
##                                                                                                ##
####################################################################################################


@app.post("/posts")
async def post_a_post(
    post: Post, authorization: str | None = Header(default=None)
):
    """
    Poste un post ! Les informations du poste sont dans post.title, post.body et le user dans authorization
    """
    logger.info(f"title : {post.title}")
    logger.info(f"body : {post.body}")
    logger.info(f"user : {authorization}")

    try:
        str_id = f"{uuid.uuid4()}"

        data = table.put_item(
            Item={
                "title": post.title,
                "body": post.body,
                "user": "USER#" + authorization,
                "id": "POST#" + str_id,
            }
        )
    except (TypeError, ValueError) as e:
        res = f"Erreur : le post n'a pas pu être posté. {e}"

    else:
        res = data

    # Doit retourner le résultat de la requête la table dynamodb
    return res


import json
from createPresignedUrl import create_presigned_url


@app.get("/posts")
async def get_all_posts(user: Union[str, None] = None):
    """
    Récupère tout les postes.
    - Si un user est présent dans le requête, récupère uniquement les siens
    - Si aucun user n'est présent, récupère TOUS les postes de la table !!
    """

    res = []

    try:
        if user:
            logger.info(f"Récupération des postes de : {user}")
            result = table.query(
                Select="ALL_ATTRIBUTES",
                KeyConditionExpression="#usr = :pk",
                ExpressionAttributeNames={"#usr": "user"},
                ExpressionAttributeValues={":pk": f"USER#{user}"},
            )
        else:
            logger.info("Récupération de tous les postes")
            result = table.scan()
            print(result)

        result = result["Items"]

        for raw_item in result:
            str_id = raw_item["id"]
            title = raw_item["title"]
            body = raw_item["body"]
            user = raw_item["user"]
            path = raw_item.get("path", "")

            item = {
                "id": str_id,
                "user": user,
                "title": title,
                "body": body,
            }

            if path:
                image = create_presigned_url(object_name=path)
                label = raw_item.get("labels", [])
                item["image"] = image
                item["labels"] = label

            res.append(item)

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des posts : {e}")
        res = f"Les posts n'ont pas pu être trouvés. Détails : {e}"

    # Doit retourner une liste de posts
    return res


@app.delete("/posts/{post_id}")
async def delete_post(
    post_id: str, authorization: str | None = Header(default=None)
):
    # Doit retourner le résultat de la requête la table dynamodb
    logger.info(f"post id : {post_id}")
    logger.info(f"user: {authorization}")

    # Récupération des infos du poste
    logger.info(f"Récupération du post: {post_id}")
    result = table.query(
        Select="ALL_ATTRIBUTES",
        KeyConditionExpression="#usr = :pk AND #id = :id",
        ExpressionAttributeNames={
            "#usr": "user",
            "#id": "id",
        },
        ExpressionAttributeValues={
            ":pk": f"USER#{authorization}",
            ":id": f"POST#{post_id}",
        },
    )

    raw_item = result["Items"][0]

    # S'il y a une image on la supprime de S3
    path = raw_item.get("path", "")
    if path:
        logger.info(f"Suppression de l'image sur S3: {bucket}/{path}")
        try:
            s3_client.delete_object(Bucket=bucket, Key=path)
        except Exception as e:
            print(f"Erreur lors de la suppression de l'image : {e}")

    # Suppression de la ligne dans la base dynamodb
    logger.info("Suppression de la ligne dans la base dynamodb")
    try:
        item = table.delete_item(
            Key={"user": f"USER#{authorization}", "id": f"POST#{post_id}"}
        )
    except Exception as e:
        print(f"Erreur lors de la suppression de l'élément : {e}")

    # Retourne le résultat de la requête de suppression
    return item


#################################################################################################
##                                                                                             ##
##                                 NE PAS TOUCHER CETTE PARTIE                                 ##
##                                                                                             ##
## 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 ##
@app.get("/signedUrlPut")
async def get_signed_url_put(
    filename: str,
    filetype: str,
    postId: str,
    authorization: str | None = Header(default=None),
):
    return getSignedUrl(filename, filetype, postId, authorization)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")

## ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ##
##                                                                                                ##
####################################################################################################
