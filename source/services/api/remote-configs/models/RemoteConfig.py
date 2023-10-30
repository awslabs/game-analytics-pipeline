"""
This module contains RemoteConfig class.
"""
from typing import Any, List

from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from utils import constants


class RemoteConfig:
    """
    This class represents a RemoteConfig.
    """

    def __init__(self, data: dict[str, Any]):
        self.__data = data

    @staticmethod
    def get_actives(dynamodb: DynamoDBServiceResource) -> List["RemoteConfig"]:
        """
        This method returns actived RemoteConfigs
        """
        response = dynamodb.Table(constants.REMOTE_CONFIGS_TABLE).scan()
        return [RemoteConfig(item) for item in response["Items"]]

    @property
    def reference_value(self) -> str:
        """
        This method returns reference_value.
        """
        return self.__data["reference_value"]

    @property
    def remote_config_name(self) -> str:
        """
        This method returns remote_config_name.
        """
        return self.__data["remote_config_name"]
