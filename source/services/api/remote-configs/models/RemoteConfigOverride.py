"""
This module contains RemoteConfigOverride class.
"""
from typing import Any, List

from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from utils import constants


class RemoteConfigOverride:
    """
    This class represents a remote config override.
    """

    def __init__(self, data: dict[str, Any]):
        self.__data = data

    @staticmethod
    def get_actives(
        dynamodb: DynamoDBServiceResource, remote_config_name
    ) -> List["RemoteConfigOverride"]:
        """
        This method returns actived RemoteConfigOverride.
        """
        response = dynamodb.Table(constants.REMOTE_CONFIGS_OVERRIDES_TABLE).query(
            IndexName="remote_config_name-active-index",
            KeyConditionExpression=Key("remote_config_name").eq(remote_config_name)
            & Key("active").eq(1),
        )
        return [RemoteConfigOverride(item) for item in response["Items"]]

    @property
    def audience_name(self) -> str:
        """
        This property retus audience_name.
        """
        return self.__data["audience_name"]

    @property
    def override_type(self) -> str:
        """
        This property retus override_type.
        """
        return self.__data["override_type"]

    @property
    def override_value(self) -> str:
        """
        This property retus override_value.
        """
        return self.__data["override_value"]
