"""
This module contains ABTest class.
"""
from decimal import Decimal
from typing import Any, List

from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from utils import constants


class ABTest:
    """
    This class represents an ABTest.
    """

    def __init__(self, database: DynamoDBServiceResource, data: dict[str, Any]):
        self.__assert_data(data)
        self.__database = database
        self.__data = data

    @classmethod
    def from_name(cls, database: DynamoDBServiceResource, abtest_name: str):
        """
        This method creates an instance of ABTest from abtest_name. It fetches database.
        It returns None if there is no ABTest with this name.
        """
        response = database.Table(constants.TABLE_ABTESTS).get_item(
            Key={"abtest_name": abtest_name}
        )
        if item := response.get("Item"):
            return cls(database, item)

    @staticmethod
    def get_all(database: DynamoDBServiceResource) -> List["ABTest"]:
        """
        This static method returns all abtests.
        """
        response = database.Table(constants.TABLE_ABTESTS).scan()
        return [ABTest(database, item) for item in response["Items"]]

    @staticmethod
    def exists(database: DynamoDBServiceResource, abtest_name: str) -> bool:
        """
        This property returns True if ABTest exists, else False.
        """
        response = database.Table(constants.TABLE_ABTESTS).get_item(
            Key={"abtest_name": abtest_name}
        )
        return "Item" in response

    @property
    def abtest_name(self) -> str:
        """
        This method returns abtest_name.
        """
        return self.__data["abtest_name"]

    @property
    def target_user_percent(self) -> int:
        """
        This method returns target_user_percent.
        """
        target_user_percent = self.__data["target_user_percent"]
        return (
            Decimal(target_user_percent)
            if isinstance(target_user_percent, (float, int))
            else target_user_percent
        )

    @property
    def variants(self) -> list[str]:
        """
        This method returns variants.
        """
        return self.__data["variants"]

    def delete(self):
        """
        This method deletes abtest from database.
        """
        self.__database.Table(constants.TABLE_ABTESTS).delete_item(
            Key={"abtest_name": self.abtest_name}
        )

    def purge(self):
        """
        This method purges users abtest.
        """
        users_abtests_table = self.__database.Table(constants.TABLE_USERS_ABTESTS)
        response = users_abtests_table.query(
            IndexName="abtest_name-index",
            KeyConditionExpression=Key("abtest_name").eq(self.abtest_name),
        )
        with users_abtests_table.batch_writer() as batch:
            for item in response["Items"]:
                batch.delete_item(Key=item)

    def to_dict(self) -> dict[str, Any]:
        """
        This method returns a dict that represents the ABTest.
        """
        return self.__data

    def update_database(self):
        """
        This method updates RemoteConfigCondition to database.
        """
        self.__database.Table(constants.TABLE_ABTESTS).put_item(
            Item={
                "abtest_name": self.abtest_name,
                "target_user_percent": self.target_user_percent,
                "variants": self.variants,
            }
        )

    def __assert_data(self, data: dict[str, Any]):
        abtest_name = data["abtest_name"]
        target_user_percent = data["target_user_percent"]
        variants = data["variants"]

        assert (
            isinstance(abtest_name, str) and abtest_name != ""
        ), "`abtest_name` should be non-empty string"
        assert (
            isinstance(target_user_percent, (int, Decimal))
            and 0 <= target_user_percent <= 100
        ), "`target_user_percent` should be integer between 0 and 100"
        assert (
            isinstance(variants, list) and len(variants) > 0
        ), "`variants` should be a non-empty list of strings"
        for variant in variants:
            assert isinstance(
                variant, str
            ), "`variants` should be a non-empty list of strings"
