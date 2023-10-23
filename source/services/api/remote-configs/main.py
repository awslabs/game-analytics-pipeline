"""
Lambda handler
"""
import os
import random

import boto3
from boto3.dynamodb.conditions import Attr, Key


dynamodb = boto3.resource("dynamodb")

abtests_table = dynamodb.Table(os.environ["ABTESTS_TABLE"])
remote_configs_table = dynamodb.Table(os.environ["REMOTE_CONFIGS_TABLE"])
users_abtests_table = dynamodb.Table(os.environ["USERS_ABTESTS_TABLE"])


def handler(event: dict, context: dict):
    """
    lambda handler
    """
    print("Attempting to retrieve remote configs.")
    print(f"Event: {event}")
    print(f"Context: {context}")

    user_id = event["userId"]
    remote_configs = {}

    remote_configs_result = remote_configs_table.query(
        IndexName="active-index",
        KeyConditionExpression=Key("active").eq(1),
    )

    for remote_config in remote_configs_result.get("Items", []):
        value = remote_config["reference_value"]
        value_origin = "reference_value"

        abtests_result = abtests_table.query(
            IndexName="active-index",
            KeyConditionExpression=Key("active").eq(1),
            FilterExpression=Attr("remote_config_ID").eq(remote_config["ID"])
            & Attr("paused").eq(False),
        )

        if abtest := next(iter(abtests_result.get("Items", [])), None):
            users_abtests_result = users_abtests_table.get_item(
                Key={"uid": user_id, "abtest_ID": abtest.get("ID")}
            )

            if "Item" not in users_abtests_result:
                is_in_test = random.randint(0, 99) < abtest.get("target_user_percent")
                value_origin = "abtest" if is_in_test else "reference_value"

                if is_in_test:
                    choices = [remote_config.get("reference_value")] + abtest.get(
                        "variants", []
                    )
                    value = random.choice(choices)

                users_abtests_table.put_item(
                    Item={
                        "uid": user_id,
                        "abtest_ID": abtest.get("ID"),
                        "is_in_test": is_in_test,
                        "value": value,
                    }
                )
            else:
                value = users_abtests_result["Item"]["value"]
                value_origin = (
                    "abtest"
                    if users_abtests_result["Item"]["is_in_test"]
                    else "reference_value"
                )

        remote_configs[remote_config["name"]] = {
            "value": value,
            "value_origin": value_origin,
        }

    return remote_configs
