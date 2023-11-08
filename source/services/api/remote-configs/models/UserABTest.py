"""
This module contains UserABTest class.
"""
import random

from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from models.ABTest import ABTest
from utils import constants


class UserABTest:
    """
    This class represents all ABTests groups for a user.
    """

    def __init__(self, dynamodb: DynamoDBServiceResource, uid: str, abtest: ABTest):
        self.__abtest = abtest
        self.__uid = uid
        self.__dynamodb = dynamodb

        response = dynamodb.Table(constants.USERS_ABTESTS_TABLE).get_item(
            Key={"uid": uid, "abtest_name": abtest.abtest_name}
        )
        if item := response.get("Item"):
            self.__data = item
            self.__exists = True
        else:
            self.__data = {}
            self.__exists = False

    @property
    def exists(self) -> bool:
        """
        This property returns True if UserABTest exists in database, else False.
        """
        return self.__exists

    @property
    def is_in_test(self) -> bool:
        """
        This property returns UserABTest is_in_test.
        """
        return self.__data["is_in_test"]

    @property
    def value(self) -> str:
        """
        This property returns UserABTest value.
        """
        return self.__data["value"]

    def set_group(self, reference_value: str):
        """
        This method sets user in abtest group.
        """
        self.__data["is_in_test"] = (
            random.randint(0, 99) < self.__abtest.target_user_percent
        )
        self.__data["value"] = (
            random.choice([reference_value] + self.__abtest.variants)
            if self.is_in_test
            else reference_value
        )
        self.__dynamodb.Table(constants.USERS_ABTESTS_TABLE).put_item(
            Item={
                "uid": self.__uid,
                "abtest_name": self.__abtest.abtest_name,
                "is_in_test": self.is_in_test,
                "value": self.value,
            }
        )
