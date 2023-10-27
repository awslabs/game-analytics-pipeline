"""
Lambda handler
"""
from typing import Any

import boto3

from models.ABTest import ABTest
from models.Audience import Audience
from models.RemoteConfig import RemoteConfig
from models.RemoteConfigOverride import RemoteConfigOverride
from models.UserABTest import UserABTest


dynamodb = boto3.resource("dynamodb")


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

    # NEW

    for remote_config in RemoteConfig.get_actives(dynamodb):
        overrides = RemoteConfigOverride.get_actives(
            dynamodb, remote_config.remote_config_name
        )
        if not overrides:
            remote_configs[remote_config.remote_config_name] = {
                "value": remote_config.reference_value,
                "value_origin": "reference_value",
            }
            continue

        for override in overrides:
            if __match_audience(override.audience_name, user_data):
                if override.override_type == "fixed":
                    remote_configs[remote_config.remote_config_name] = {
                        "value": override.override_value,
                        "value_origin": "reference_value",
                    }
                    break

                # override_type == abtest
                abtest = ABTest(dynamodb, override.override_value)
                user_abtest = UserABTest(dynamodb, user_ID, abtest)

                if not user_abtest.exists:
                    user_abtest.set_group(remote_config.reference_value)

                remote_configs[remote_config.remote_config_name] = {
                    "value": user_abtest.value,
                    "value_origin": "abtest"
                    if user_abtest.is_in_test
                    else "reference_value",
                }
                break
        else:
            # No audience matches, we give the reference_value
            remote_configs[remote_config.remote_config_name] = {
                "value": remote_config.reference_value,
                "value_origin": "reference_value",
            }

    return remote_configs


def __match_audience(audience_name: str, user_data: dict[str, Any]) -> bool:
    audience = Audience(dynamodb, audience_name, user_data)
    return audience.target_applications and audience.target_countries
