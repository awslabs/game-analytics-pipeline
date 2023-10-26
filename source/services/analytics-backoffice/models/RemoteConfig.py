"""
This module contains RemoteConfig class.
"""
from typing import Any, List

from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from utils import constants


class RemoteConfig:
    """
    This class represents a mobile application configuration that we can manage remotely.
    """

    def __init__(self, database: DynamoDBServiceResource, data: dict[str, Any]):
        self.__assert_data(data)
        self.__database = database
        self.__data = data

    @classmethod
    def from_name(cls, database: DynamoDBServiceResource, remote_config_name: str):
        """
        This method creates an instance of RemoteConfig from remote_config_name. It fetches database.
        It returns None if there is no RemoteConfig with this name.
        """
        response = database.Table(constants.TABLE_REMOTE_CONFIGS).get_item(
            Key={"remote_config_name": remote_config_name}
        )
        if item := response.get("Item"):
            return cls(database, item)

    @staticmethod
    def get_all(database: DynamoDBServiceResource) -> List["RemoteConfig"]:
        """
        This static method returns all remote configs.
        """
        response = database.Table(constants.TABLE_REMOTE_CONFIGS).scan()
        return [RemoteConfig(database, item) for item in response["Items"]]

    @staticmethod
    def exists(database: DynamoDBServiceResource, remote_config_name: str) -> bool:
        """
        This property returns True if RemoteConfig exists, else False.
        """
        response = database.Table(constants.TABLE_REMOTE_CONFIGS).get_item(
            Key={"remote_config_name": remote_config_name}
        )
        return "Item" in response

    @property
    def activated(self) -> bool:
        """
        This method returns True if the RemoteConfig is activated else False.
        """
        return self.active == 1

    @property
    def active(self) -> int:
        """
        This method returns 1 if the RemoteConfig is activated else 0.
        """
        if "active" not in self.__data:
            # Check if this remote Config already exists in database.
            response = self.__database.Table(constants.TABLE_REMOTE_CONFIGS).get_item(
                Key={"remote_config_name": self.remote_config_name}
            )
            self.__data["active"] = response.get("Item", {}).get("active", 0)
        return self.__data["active"]

    @property
    def description(self) -> str:
        """
        This method returns description.
        """
        return self.__data["description"]

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

    def activate(self):
        """
        This method activates RemoteConfig in database.
        """
        self.__database.Table(constants.TABLE_REMOTE_CONFIGS).update_item(
            Key={"remote_config_name": self.remote_config_name},
            AttributeUpdates={
                "active": {"Value": 1, "Action": "PUT"},
            },
        )

    def delete(self):
        """
        This method deletes RemoteConfig from database.
        """
        self.__database.Table(constants.TABLE_REMOTE_CONFIGS).delete_item(
            Key={"remote_config_name": self.remote_config_name}
        )

    def to_dict(self) -> dict[str, Any]:
        """
        This method returns a dict that represents the RemoteConfig.
        """
        return self.__data

    def update_database(self):
        """
        This method creates RemoteConfig in database.
        """
        self.__database.Table(constants.TABLE_REMOTE_CONFIGS).put_item(
            Item={
                "remote_config_name": self.remote_config_name,
                "active": self.active,
                "description": self.description,
                "reference_value": self.reference_value,
            }
        )

    def __assert_data(self, data: dict[str, Any]):
        remote_config_name = data["remote_config_name"]
        description = data["description"]
        reference_value = data["reference_value"]

        assert (
            isinstance(remote_config_name, str) and remote_config_name != ""
        ), "`remote_config_name` should be non-empty string"
        assert isinstance(description, str), "`description` should be string"
        assert isinstance(reference_value, str), "`reference_value` should be string"
