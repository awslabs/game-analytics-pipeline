"""
This module contains Audience class.
"""
from typing import Any, List
from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from utils import constants


class Audience:
    """
    This class represents an audience.
    """

    def __init__(self, data: dict[str, Any]):
        self.__data = data

    @staticmethod
    def get_users_audiences(
        dynamodb: DynamoDBServiceResource, uid: str
    ) -> List["Audience"]:
        """
        This static method returns a list of all Audiences for uid.
        """
        response = dynamodb.Table(constants.USERS_AUDIENCES_TABLE).query(
            IndexName="uid-index", KeyConditionExpression=Key("uid").eq(uid)
        )

        return [Audience(item) for item in response["Items"]]

    @property
    def audience_name(self) -> str:
        """
        This property returns audience_name.
        """
        return self.__data["audience_name"]
