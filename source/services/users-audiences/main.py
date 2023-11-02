"""
This module lambda assigns audiences to users.
"""
from datetime import datetime, timedelta
from time import sleep, time

import boto3

from utils import constants


athena = boto3.client("athena")
dynamodb = boto3.resource("dynamodb")


def handler(event: dict, context: dict):
    """
    lambda handler
    """
    print("Assigning audiences to users.")
    print(f"Event: {event}")
    print(f"Context: {context}")

    yesterday = datetime.now() - timedelta(days=1)

    query_IDs: dict[str, str] = {}
    users_audiences: list[tuple[str, str]] = []  # tuple[0] == uid, tuple[1] == audience_name

    dynamodb_response = dynamodb.Table(constants.AUDIENCES_TABLE).scan()
    for audience in dynamodb_response["Items"]:
        athena_response = athena.start_query_execution(
            QueryString=f"""
                SELECT DISTINCT(json_extract_scalar(user, '$.user_id'))
                FROM {constants.ANALYTICS_TABLE}
                WHERE ({audience['condition']})
                    AND year>='{yesterday.year}'
                    AND month>='{str(yesterday.month).zfill(2)}'
                    AND day>='{str(yesterday.day).zfill(2)}'
            """,
            QueryExecutionContext={"Database": constants.ANALYTICS_DATABASE},
            ResultConfiguration={
                "OutputLocation": f"s3://{constants.ANALYTICS_BUCKET}/athena_query_results/"
            },
        )
        query_IDs[athena_response["QueryExecutionId"]] = audience["audience_name"]

    # Waiting for queries to execute
    for query_ID, audience_name in query_IDs.items():
        print(f"Waiting {audience_name} query...")
        while True:
            sleep(0.5)  # To avoid spamming requests
            query_status = athena.get_query_execution(QueryExecutionId=query_ID)[
                "QueryExecution"
            ]["Status"]
            if query_status["State"] not in ("QUEUED", "RUNNING"):
                break

        if query_status["State"] == "FAILED":
            print(
                f"ERROR with {audience_name} audience : {query_status['StateChangeReason']}"
            )
            continue

        print(f"Audience {audience_name} processing...")
        # Get Athena Query Results
        query_results = athena.get_query_results(QueryExecutionId=query_ID)
        result_set = query_results["ResultSet"]

        users_audiences.extend(
            (row["Data"][0]["VarCharValue"], audience_name)
            for row in result_set["Rows"][1:]
        )

    print(f"Filling the {constants.USERS_AUDIENCES_TABLE} table in progress...")
    expires_timestamp = int(time()) + (60 * 60 * 24 * 30)  # 30 days
    with dynamodb.Table(constants.USERS_AUDIENCES_TABLE).batch_writer() as batch:
        for uid, audience_name in users_audiences:
            batch.put_item(
                Item={
                    "uid": uid,
                    "audience_name": audience_name,
                    "expires_timestamp": expires_timestamp,
                }
            )

    raise SystemError("Try Alarme")
