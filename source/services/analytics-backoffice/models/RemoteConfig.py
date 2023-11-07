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
        self.__assert_data(database, data)
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
    def application_IDs(self) -> list[str]:
        """
        This method returns application_IDs.
        """
        return self.__data["applications"]

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
                "description": self.description,
                "reference_value": self.reference_value,
                "applications": self.application_IDs,
            }
        )

    def __assert_data(self, database: DynamoDBServiceResource, data: dict[str, Any]):
        application_IDs = data["applications"]
        remote_config_name = data["remote_config_name"]
        description = data["description"]
        reference_value = data["reference_value"]

        assert isinstance(
            application_IDs, list
        ), "`application_IDs` should be a list of non-empty string"
        assert (
            isinstance(remote_config_name, str) and remote_config_name != ""
        ), "`remote_config_name` should be non-empty string"
        assert isinstance(description, str), "`description` should be string"
        assert isinstance(reference_value, str), "`reference_value` should be string"

        for application_ID in application_IDs:
            assert (
                application_ID != ""
            ), "`application_IDs` should be a list of non-empty string"
            response = database.Table(constants.TABLE_APPLICATIONS).get_item(
                Key={"application_id": application_ID}
            )
            assert (
                "Item" in response
            ), f"`There is no application with ID : {application_ID}`"
