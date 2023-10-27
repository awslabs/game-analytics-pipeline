"""
This module contains RemoteConfigConditions class.
"""
from typing import Any
from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from utils import constants


class Audience:
    """
    This class represents an audience.
    """

    def __init__(
        self,
        dynamodb: DynamoDBServiceResource,
        audience_name: str,
        user_data: dict[str, Any],
    ):
        response = dynamodb.Table(constants.AUDIENCES_TABLE).query(
            IndexName="audience_name-index",
            KeyConditionExpression=Key("audience_name").eq(audience_name),
        )
        self.__conditions = {item["condition_type"]: item["condition_value"] for item in response["Items"]}
        self.__user_data = user_data

    @property
    def target_applications(self) -> bool:
        """
        This method checks if remote config is available for user application.
        """
        if target_applications := self.__conditions.get("target_applications"):
            return self.__user_data["application_ID"] in target_applications
        return True

    @property
    def target_countries(self) -> bool:
        """
        This method checks if remote config is available for user country.
        """
        if target_countries := self.__conditions.get("target_countries"):
            return self.__user_data["country"] in target_countries
        return True
