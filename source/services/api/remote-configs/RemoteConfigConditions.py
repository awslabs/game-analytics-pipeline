"""
This module contains functions to verify remote config conditions.
"""
import os
from typing import Any

from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource


class RemoteConfigConditions:
    """
    This class represents all conditions for a remote config.
    """

    def __init__(
        self,
        dynamodb: DynamoDBServiceResource,
        remote_config_ID: str,
        user_data: dict[str, Any],
    ):
        response = dynamodb.Table(os.environ["REMOTE_CONFIGS_CONDITIONS_TABLE"]).query(
            KeyConditionExpression=Key("remote_config_ID").eq(remote_config_ID),
        )
        self.__conditions = {
            item["condition_type"]: item["condition_value"]
            for item in response["Items"]
        }
        self.__user_data = user_data

    @property
    def application_available(self) -> bool:
        """
        This method checks if remote config is available for user application.
        """
        if available_applications := self.__conditions.get("available_applications"):
            return self.__user_data["application_ID"] in available_applications
        return True

    @property
    def country_available(self) -> bool:
        """
        This method checks if remote config is available for user country.
        """
        if available_countries := self.__conditions.get("available_countries"):
            return self.__user_data["country"] in available_countries
        return True
