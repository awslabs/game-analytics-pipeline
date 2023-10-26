"""
This module contains Audience class.
"""
from decimal import Decimal
from typing import Any, List

from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from utils import constants


class Audience:
    """
    This class represents an Audience.
    """

    __condition_types = ("target_applications", "target_countries")

    def __init__(self, database: DynamoDBServiceResource, data: dict[str, Any]):
        self.__assert_data(data)
        self.__database = database
        self.__data = data

    @classmethod
    def from_database(
        cls, database: DynamoDBServiceResource, audience_name: str, condition_type: str
    ):
        """
        This method creates an instance of Audience from audience_name and condition_type by fetching database.
        It returns None if there is no Audience with this audience_name and the same condition_type.
        """
        response = database.Table(constants.TABLE_AUDIENCES).get_item(
            Key={"audience_name": audience_name, "condition_type": condition_type}
        )
        if item := response.get("Item"):
            return cls(database, item)

    @staticmethod
    def get_all(database: DynamoDBServiceResource) -> List["Audience"]:
        """
        This static method returns all audiences.
        """
        response = database.Table(constants.TABLE_AUDIENCES).scan()
        return [Audience(database, item) for item in response["Items"]]

    @staticmethod
    def exists(database: DynamoDBServiceResource, audience_name: str) -> bool:
        """
        This property returns True if Audience exists, else False.
        """
        response = database.Table(constants.TABLE_AUDIENCES).query(
            KeyConditionExpression=Key("audience_name").eq(audience_name)
        )
        return len(response["Items"]) > 0

    @property
    def audience_name(self) -> str:
        """
        This method returns audience_name.
        """
        return self.__data["audience_name"]

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

    @property
    def description(self) -> str:
        """
        This method returns description.
        """
        return self.__data["description"]

    def delete(self):
        """
        This method deletes audience from database.
        """
        self.__database.Table(constants.TABLE_AUDIENCES).delete_item(
            Key={
                "audience_name": self.audience_name,
                "condition_type": self.condition_type,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        """
        This method returns a dict that represents the Audience.
        """
        return self.__data

    def update_database(self):
        """
        This method updates RemoteConfigCondition to database.
        """
        self.__database.Table(constants.TABLE_AUDIENCES).put_item(
            Item={
                "audience_name": self.audience_name,
                "condition_type": self.condition_type,
                "condition_value": self.condition_value,
                "description": self.description,
            }
        )

    def __assert_data(self, data: dict[str, Any]):
        audience_name = data["audience_name"]
        condition_type = data["condition_type"]
        condition_value = data["condition_value"]
        description = data["description"]

        assert (
            isinstance(audience_name, str) and audience_name != ""
        ), "`audience_name` should be non-empty string"
        assert (
            condition_type in self.__condition_types
        ), f"condition_type {condition_type} not allowed : {self.__condition_types}"
        assert condition_value is not None, "`condition_value` can NOT be null"
        assert isinstance(description, str), "`description` should be string"
