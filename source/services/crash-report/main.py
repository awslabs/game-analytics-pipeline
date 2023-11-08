"""
This lambda analyses apps every hours.
"""
from datetime import datetime
import json
from time import sleep, time
from typing import Any

import boto3
import requests

from utils import constants


athena = boto3.client("athena")
dynamodb = boto3.resource("dynamodb")
secrets_manager = boto3.client("secretsmanager")


def handler(event: dict, context: dict):
    """
    lambda handler
    """
    print("App crash analysis.")
    print(f"Event: {event}")
    print(f"Context: {context}")

    slack_channel, slack_token = __slack_secrets()

    crashes_rates: list[dict[str, Any]] = []
    query_IDs: dict[str, str] = {}

    with open("assets/crash_query.sql", encoding="UTF-8") as f:
        base_query = f.read()

    dynamodb_response = dynamodb.Table(constants.APPLICATIONS_TABLE).scan()
    for item in dynamodb_response["Items"]:
        application_name = item["application_name"]
        athena_response = athena.start_query_execution(
            QueryString=base_query.replace("%%APPLICATION_NAME%%", application_name),
            QueryExecutionContext={"Database": constants.ANALYTICS_DATABASE},
            ResultConfiguration={
                "OutputLocation": f"s3://{constants.ANALYTICS_BUCKET}/athena_query_results/"
            },
        )
        query_IDs[application_name] = athena_response["QueryExecutionId"]

    # Waiting for queries to execute
    for application_name, query_ID in query_IDs.items():
        __wait_athena_query(application_name, query_ID)

        # Get Athena Query Results
        query_results = athena.get_query_results(QueryExecutionId=query_ID)
        result_set = query_results["ResultSet"]

        # Search index for each column
        for i, column in enumerate(result_set["ResultSetMetadata"]["ColumnInfo"]):
            match column["Name"]:
                case "app_version":
                    app_version_index = i
                case "rate_impacted_users":
                    rate_impacted_users_index = i
                case "rate_crash_free_sessions":
                    rate_crash_free_sessions_index = i

        for row in result_set["Rows"][1:]:
            rate_impacted_users = float(
                row["Data"][rate_impacted_users_index]["VarCharValue"]
            )
            rate_crash_free_sessions = float(
                row["Data"][rate_crash_free_sessions_index]["VarCharValue"]
            )
            if rate_crash_free_sessions <= constants.RATE_CRASH_FREE_SESSIONS_THRESHORD:
                app_version = row["Data"][app_version_index]["VarCharValue"]
                crash_rate = {
                    "application_name": application_name,
                    "app_version": app_version,
                    "rate_impacted_users": rate_impacted_users,
                    "rate_crash_free_sessions": rate_crash_free_sessions,
                }
                crashes_rates.append(crash_rate)
                if not __crash_reported(application_name, app_version):
                    __slack_message(slack_channel, slack_token, crash_rate)

    expires_timestamp = int(time()) + (60 * 60 * 24)  # 24 hours
    with dynamodb.Table(constants.CRASHES_TABLE).batch_writer() as batch:
        for crash_rate in crashes_rates:
            batch.put_item(
                Item={
                    "application_name": crash_rate["application_name"],
                    "app_version": crash_rate["app_version"],
                    "expires_timestamp": expires_timestamp,
                }
            )


def __crash_reported(application_name: str, app_version: str) -> bool:
    response = dynamodb.Table(constants.CRASHES_TABLE).get_item(
        Key={"application_name": application_name, "app_version": app_version}
    )
    return "Item" in response


def __slack_secrets() -> tuple[str, str]:
    slack_secrets = json.loads(
        secrets_manager.get_secret_value(SecretId="slack")["SecretString"]
    )
    return slack_secrets["CRASH_CHANNEL"], slack_secrets["TOKEN"]


def __slack_message(channel: str, token: str, crash_rate: dict[str, Any]):
    application_name = crash_rate["application_name"]
    is_china = "cn" in constants.REGION_NAME

    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "attachments": [
                {
                    "title": f"Crash Report Alert - {application_name} {'CHINA' if is_china else ''} - {crash_rate['app_version']}",
                    "text": "\n".join(
                        [
                            f"• Impacted Users: {crash_rate['rate_impacted_users']}%",
                            f"• Crash Free Sessions: {crash_rate['rate_crash_free_sessions']}%",
                            f"<{constants.UNITY_CRASH_URL.replace('%%PROJECT_ID%%', constants.UNITY_PROJECTS[application_name])}|View Crash Report>",
                            "This crash will be re-evaluated in 24 hours.",
                        ]
                    ),
                    "color": "#FF0000",
                    "footer": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                }
            ],
            "channel": channel,
            "username": "Crash Report",
        },
        timeout=60,
    )
    response_data = response.json()
    if not response_data["ok"]:
        raise ValueError(f"Error during Slack process : {response_data['error']}")


def __wait_athena_query(application_name: str, query_ID: str):
    print(f"Waiting {query_ID} query for {application_name} application...")
    while True:
        sleep(0.5)  # To avoid spamming requests
        query_status = athena.get_query_execution(QueryExecutionId=query_ID)[
            "QueryExecution"
        ]["Status"]
        if query_status["State"] not in ("QUEUED", "RUNNING"):
            break

    if query_status["State"] == "FAILED":
        raise ValueError(
            f"ERROR with {application_name} application : {query_status['StateChangeReason']}"
        )
