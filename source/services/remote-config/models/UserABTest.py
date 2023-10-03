"""
This module contains UserABTests class.
"""
import random
from typing import Any

from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from utils import constants


class UserABTest:
    """
    This class represents an ABTest for a User.
    """

    def __init__(self, database: DynamoDBServiceResource, uid: str, abtest_ID: str):
        self.__database = database
        self.uid = uid
        self.abtest_ID = abtest_ID

        response = self.__database.Table(constants.TABLE_USERS_ABTESTS).get_item(
            Key={"uid": uid, "abtest_ID": self.abtest_ID}
        )
        if item := response.get("Item"):
            self.has_group = True
            self.is_in_test = item["is_in_test"]
            self.value = item["value"]
        else:
            self.has_group = False

    def set_group(
        self, target_user_percent: int, reference_value: Any, variants: list[Any]
    ):
        """
        This method sets user in a group.
        """
        self.is_in_test = random.randint(0, 99) < target_user_percent
        self.value = (
            random.choice([reference_value] + variants)
            if self.is_in_test
            else reference_value
        )
        data = {
            "uid": self.uid,
            "abtest_ID": self.abtest_ID,
            "is_in_test": self.is_in_test,
            "value": self.value,
        }
        self.__database.Table(constants.TABLE_USERS_ABTESTS).put_item(Item=data)
