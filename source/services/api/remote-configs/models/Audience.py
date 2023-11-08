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

    def __init__(self, audience_name: str):
        self.__audience_name = audience_name

    @staticmethod
    def event_based_audiences(
        dynamodb: DynamoDBServiceResource, uid: str
    ) -> List["Audience"]:
        """
        This static method returns a list of all event_based Audiences for uid.
        """
        response = dynamodb.Table(constants.USERS_AUDIENCES_TABLE).query(
            IndexName="uid-index", KeyConditionExpression=Key("uid").eq(uid)
        )

        return [Audience(item["audience_name"]) for item in response["Items"]]

    @staticmethod
    def property_based_audiences(
        dynamodb: DynamoDBServiceResource,
        user_data: dict[str, Any],
    ) -> List["Audience"]:
        """
        This static method returns a list of all property_based Audiences for uid.
        """
        response = dynamodb.Table(constants.AUDIENCES_TABLE).query(
            IndexName="type-index",
            KeyConditionExpression=Key("type").eq("property_based"),
        )

        audiences = []
        for item in response["Items"]:
            condition_str = item["condition"]
            if "&" in condition_str and "||" in condition_str:
                raise ValueError("We NOT handle & AND || in the same condition")
            if "||" in condition_str:
                audience_match = Audience.__audience_match(
                    user_data, condition_str.split("||"), "||"
                )
            else:
                # If there is only one parameter or multiple AND parameter
                audience_match = Audience.__audience_match(
                    user_data, condition_str.split("&"), "&"
                )

            if audience_match:
                audiences.append(Audience(item["audience_name"]))

        return audiences

    @property
    def audience_name(self) -> str:
        """
        This property returns audience_name.
        """
        return self.__audience_name

    @staticmethod
    def __audience_match(
        user_data: dict[str, Any], conditions: list[str], operator: str
    ) -> bool:
        for condition in conditions:
            parameter, value = condition.split("=")
            if user_data[parameter] != value and operator == "&":
                return False
            if user_data[parameter] == value and operator == "||":
                return True

        return operator == "&"
