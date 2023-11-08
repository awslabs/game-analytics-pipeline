"""
This module lambda assigns audiences to users.
"""
from collections import defaultdict
from datetime import datetime, timedelta
from time import sleep, time

import boto3
from boto3.dynamodb.conditions import Key

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

    dates = [datetime.now() - timedelta(days=i + 1) for i in range(7)]

    query_IDs = defaultdict(list)
    users_audiences: list[
        tuple[str, str]
    ] = []  # tuple[0] == uid, tuple[1] == audience_name

    dynamodb_response = dynamodb.Table(constants.AUDIENCES_TABLE).query(
        IndexName="type-index", KeyConditionExpression=Key("type").eq("event_based")
    )
    for audience in dynamodb_response["Items"]:
        for date in dates:
            athena_response = athena.start_query_execution(
                QueryString=f"""
                    SELECT json_extract_scalar(user, '$.user_id')
                    FROM {constants.ANALYTICS_TABLE}
                    WHERE ({audience['condition']})
                        AND year>='{date.year}'
                        AND month>='{str(date.month).zfill(2)}'
                        AND day>='{str(date.day).zfill(2)}'
                """,
                QueryExecutionContext={"Database": constants.ANALYTICS_DATABASE},
                ResultConfiguration={
                    "OutputLocation": f"s3://{constants.ANALYTICS_BUCKET}/athena_query_results/"
                },
            )
            query_IDs[audience["audience_name"]].append(
                athena_response["QueryExecutionId"]
            )

    # Waiting for queries to execute
    for audience_name, queries in query_IDs.items():
        uids = set()
        for query_ID in queries:
            print(f"Waiting {query_ID} query for {audience_name} audience...")
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

            query_results = athena.get_query_results(QueryExecutionId=query_ID)
            result_set = query_results["ResultSet"]

            # Get Athena Query Results
            query_results = athena.get_query_results(QueryExecutionId=query_ID)
            result_set = query_results["ResultSet"]

            for row in result_set["Rows"][1:]:
                uids.add(row["Data"][0]["VarCharValue"])

        users_audiences.extend((uid, audience_name) for uid in uids)

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
