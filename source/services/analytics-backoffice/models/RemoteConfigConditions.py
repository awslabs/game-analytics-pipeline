"""
This module contains RemoteConfigCondition class.
"""
from decimal import Decimal
from typing import Any

from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from utils import constants


class RemoteConfigCondition:
    """
    This class represents a condition for a RemoteConfig.
    """

    def __init__(self, database: DynamoDBServiceResource, data: dict[str, Any]):
        self.__assert_data(data)
        self.__database = database
        self.__data = data

    @staticmethod
    def exists(database: DynamoDBServiceResource, condition_ID: str) -> bool:
        """
        This property returns True if RemoteConfigConfition exists, else False.
        """
        response = database.Table(constants.TABLE_REMOTE_CONFIGS_CONDITIONS).query(
            KeyConditionExpression=Key("condition_ID").eq(condition_ID)
        )
        return len(response["Items"]) > 0

    @property
    def condition_ID(self) -> str:
        """
        This method returns condition_ID.
        """
        return self.__data["condition_ID"]

    @property
    def condition_type(self) -> str:
        """
        This method returns condition_type.
        """
        return self.__data["condition_type"]

    @property
    def condition_value(self) -> str:
        """
        This method returns condition_value.
        """
        condition_value = self.__data["condition_value"]
        return (
            Decimal(condition_value)
            if isinstance(condition_value, (float, int))
            else condition_value
        )

    def update_database(self):
        """
        This method updates RemoteConfigCondition to database.
        """
        self.__database.Table(constants.TABLE_REMOTE_CONFIGS_CONDITIONS).put_item(
            Item={
                "condition_ID": self.condition_ID,
                "condition_type": self.condition_type,
                "condition_value": self.condition_value,
            }
        )

    def __assert_data(self, data: dict[str, Any]):
        condition_ID = data["condition_ID"]
        condition_type = data["condition_type"]
        condition_value = data["condition_value"]

        assert isinstance(condition_ID, str)
        assert (
            condition_type in constants.ALLOWED_REMOTE_CONFIGS_CONDITIONS
        ), f"condition_type {condition_type} not allowed"
        assert condition_value is not None
