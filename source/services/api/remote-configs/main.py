"""
Lambda handler
"""
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

    remote_configs = {}
    # application_ID = event["applicationId"]
    user_ID = event["userId"]

    user_audiences = []
    user_audiences.extend(Audience.event_based_audiences(dynamodb, user_ID))
    user_audiences.extend(Audience.property_based_audiences(dynamodb, event["payload"]))

    for remote_config in RemoteConfig.get_all(dynamodb):
        overrides = RemoteConfigOverride.filter_audiences(
            dynamodb, remote_config.remote_config_name, user_audiences
        )

        if not overrides:
            # RemoteConfig has no Override or there is no audience that matches the user
            remote_configs[remote_config.remote_config_name] = {
                "value": remote_config.reference_value,
                "value_origin": "reference_value",
            }
            continue

        # If there are several overrides, it is due to an inconsistency in analytical decisions
        # So we take the first override
        override = next(iter(overrides))

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
            "value_origin": "abtest" if user_abtest.is_in_test else "reference_value",
        }

    return remote_configs
