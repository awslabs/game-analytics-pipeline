"""
Lambda handler
"""
import os
import random
from typing import Any

import boto3
from boto3.dynamodb.conditions import Attr, Key

from RemoteConfigConditions import RemoteConfigConditions


dynamodb = boto3.resource("dynamodb")

abtests_table = dynamodb.Table(os.environ["ABTESTS_TABLE"])
remote_configs_table = dynamodb.Table(os.environ["REMOTE_CONFIGS_TABLE"])
remote_configs_conditions_table = dynamodb.Table(
    os.environ["REMOTE_CONFIGS_CONDITIONS_TABLE"]
)
users_abtests_table = dynamodb.Table(os.environ["USERS_ABTESTS_TABLE"])


def handler(event: dict, context: dict):
    """
    lambda handler
    """
    print("Attempting to retrieve remote configs.")
    print(f"Event: {event}")
    print(f"Context: {context}")

    user_ID = event["userId"]
    user_data = {"application_ID": event["applicationId"], "country": event["country"]}

    remote_configs = {}

    for remote_config in __get_active_remote_configs():
        remote_config_ID = remote_config["ID"]
        if not __conditions_match(remote_config_ID, user_data):
            continue

        value = remote_config["reference_value"]
        value_origin = "reference_value"

        if abtest := __get_active_abtest(remote_config_ID):

            if user_abtest := __get_user_abtest(user_ID, abtest["ID"]):
                value = user_abtest["value"]
                value_origin = (
                    "abtest"
                    if user_abtest["is_in_test"]
                    else "reference_value"
                )

            else:
                is_in_test = random.randint(0, 99) < abtest.get("target_user_percent")
                value_origin = "abtest" if is_in_test else "reference_value"

                if is_in_test:
                    choices = [remote_config.get("reference_value")] + abtest.get(
                        "variants", []
                    )
                    value = random.choice(choices)

                users_abtests_table.put_item(
                    Item={
                        "uid": user_ID,
                        "abtest_ID": abtest.get("ID"),
                        "is_in_test": is_in_test,
                        "value": value,
                    }
                )

        remote_configs[remote_config["name"]] = {
            "value": value,
            "value_origin": value_origin,
        }

    return remote_configs

def __conditions_match(remote_config_ID: str, user_data: dict[str, Any]) -> bool:
    conditions = RemoteConfigConditions(
        dynamodb, remote_config_ID, user_data
    )
    return bool(
        conditions.application_available and conditions.country_available
    )

def __get_active_abtest(remote_config_ID: str):
    response = abtests_table.query(
        IndexName="active-index",
        KeyConditionExpression=Key("active").eq(1),
        FilterExpression=Attr("remote_config_ID").eq(remote_config_ID)
        & Attr("paused").eq(False),
    )
    return next(iter(response["Items"]), None)

def __get_active_remote_configs():
    response = remote_configs_table.query(
        IndexName="active-index",
        KeyConditionExpression=Key("active").eq(1),
    )
    return response["Items"]

def __get_user_abtest(user_ID: str, abtest_ID: str):
    response = users_abtests_table.get_item(
        Key={"uid": user_ID, "abtest_ID": abtest_ID}
    )
    return response.get("Item")
