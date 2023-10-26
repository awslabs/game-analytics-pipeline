"""
This module contains RemoteConfigOverride class.
"""
from time import time
from typing import Any, List
from uuid import uuid4

from boto3.dynamodb.conditions import Attr, Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from models.ABTest import ABTest
from utils import constants


class RemoteConfigOverride:
    """
    This class represents a RemoteConfigOverride.
    """

    __override_types = ("abtest", "fixed")

    def __init__(self, database: DynamoDBServiceResource, data: dict[str, Any]):
        self.__database = database
        self.__assert_data(data)
        self.__data = data

    @classmethod
    def from_database(
        cls,
        database: DynamoDBServiceResource,
        remote_config_name: str,
        audience_name: str,
    ):
        """
        This method creates an instance of RemoteConfigOverride by fetching database.
        """
        response = database.Table(constants.TABLE_REMOTE_CONFIGS_OVERRIDES).get_item(
            Key={
                "remote_config_name": remote_config_name,
                "audience_name": audience_name,
            }
        )
        if item := response.get("Item"):
            return cls(database, item)

    @staticmethod
    def from_abtest_name(
        database: DynamoDBServiceResource,
        abtest_name: str,
        exclude: "RemoteConfigOverride | None" = None,
    ) -> List["RemoteConfigOverride"]:
        """
        This method returns a list of RemoteConfigOverride that have <abtest_name>.
        """
        response = database.Table(constants.TABLE_REMOTE_CONFIGS_OVERRIDES).query(
            IndexName="override_type-index",
            KeyConditionExpression=Key("override_type").eq("abtest"),
            FilterExpression=Attr("override_value").eq(abtest_name),
        )
        return [
            item
            for item in response["Items"]
            if exclude is None
            or exclude.remote_config_name != item["remote_config_name"]
            or exclude.audience_name != item["audience_name"]
        ]

    @staticmethod
    def from_audience_name(
        database: DynamoDBServiceResource, audience_name: str
    ) -> List["RemoteConfigOverride"]:
        """
        This method returns a list of RemoteConfigOverride that have <audience_name>.
        """
        response = database.Table(constants.TABLE_REMOTE_CONFIGS_OVERRIDES).query(
            IndexName="audience_name-index",
            KeyConditionExpression=Key("audience_name").eq(audience_name),
        )
        return [RemoteConfigOverride(database, item) for item in response["Items"]]

    @property
    def activated(self) -> bool:
        """
        This property returns True if RemoteConfigOverride is activated else False.
        """
        return self.active == 1

    @property
    def active(self) -> int:
        """
        This property returns 1 if RemoteConfigOverride is activated else 0.
        """
        if "active" not in self.__data:
            response = self.__database.Table(
                constants.TABLE_REMOTE_CONFIGS_OVERRIDES
            ).get_item(
                Key={
                    "remote_config_name": self.remote_config_name,
                    "audience_name": self.audience_name,
                }
            )
            self.__data["active"] = response.get("Item", {}).get("active", 0)
        return self.__data["active"]

    @property
    def audience_name(self) -> str:
        """
        This property returns audience_name.
        """
        return self.__data["audience_name"]

    @property
    def override_type(self) -> str:
        """
        This property returns override_type.
        """
        return self.__data["override_type"]

    @property
    def override_value(self) -> Any:
        """
        This property returns override_value.
        """
        return self.__data["override_value"]

    @property
    def remote_config_name(self) -> str:
        """
        This property returns remote_config_name.
        """
        return self.__data["remote_config_name"]

    @property
    def start_timestamp(self) -> int:
        """
        This property returns start_timestamp.
        """
        return self.__data["start_timestamp"]

    def activate(self, activated: bool):
        """
        This method activates/deactivates RemoteConfigOverride.
        """
        if activated:
            attribute_updates = {
                "active": {"Value": 1, "Action": "PUT"},
                "start_timestamp": {"Value": int(time()), "Action": "PUT"},
            }
        else:
            attribute_updates = {
                "active": {"Value": 0, "Action": "PUT"},
                "start_timestamp": {"Action": "DELETE"},
            }
            self.fill_history({"override_value": self.override_value})

        self.__database.Table(constants.TABLE_REMOTE_CONFIGS_OVERRIDES).update_item(
            Key={
                "remote_config_name": self.remote_config_name,
                "audience_name": self.audience_name,
            },
            AttributeUpdates=attribute_updates,
        )

    def delete(self):
        """
        This method deletes RemoteConfigOverride from database.
        """
        self.__database.Table(constants.TABLE_REMOTE_CONFIGS_OVERRIDES).delete_item(
            Key={
                "remote_config_name": self.remote_config_name,
                "audience_name": self.audience_name,
            }
        )

    def fill_history(self, override_data: dict[str, Any]):
        """
        This method fills remote config overrides history.
        """
        self.__database.Table(
            constants.TABLE_REMOTE_CONFIGS_OVERRIDES_HISTORY
        ).put_item(
            Item={
                "ID": str(uuid4()),
                "type": self.override_type,
                "remote_config_name": self.remote_config_name,
                "audience_name": self.audience_name,
                "start_timestamp": self.start_timestamp,
                "end_timestamp": int(time()),
                "override_data": override_data,
            }
        )

    def fix_value(self, new_value: str, override: ABTest):
        """
        This method fix value.
        """
        if self.audience_name == "ALL":
            self.__database.Table(constants.TABLE_REMOTE_CONFIGS).update_item(
                Key={"remote_config_name": self.remote_config_name},
                AttributeUpdates={
                    "reference_value": {"Value": new_value, "Action": "PUT"},
                },
            )
            self.delete()
        else:
            self.__database.Table(constants.TABLE_REMOTE_CONFIGS_OVERRIDES).update_item(
                Key={
                    "remote_config_name": self.remote_config_name,
                    "audience_name": self.audience_name,
                },
                AttributeUpdates={
                    "override_type": {"Value": "fixed", "Action": "PUT"},
                    "override_value": {"Value": new_value, "Action": "PUT"},
                    "start_timestamp": {"Value": int(time()), "Action": "PUT"},
                },
            )

        override_data = override.to_dict() | {"promoted_value": new_value}
        self.fill_history(override_data=override_data)

    def update_database(self):
        """
        This method updates RemoteConfigOverride to database.
        """
        self.__database.Table(constants.TABLE_REMOTE_CONFIGS_OVERRIDES).put_item(
            Item={
                "remote_config_name": self.remote_config_name,
                "audience_name": self.audience_name,
                "active": self.active,
                "override_type": self.override_type,
                "override_value": self.override_value,
            }
        )

    def __assert_data(self, data: dict[str, Any]):
        audience_name = data["audience_name"]
        override_type = data["override_type"]
        override_value = data["override_value"]
        remote_config_name = data["remote_config_name"]

        assert audience_name and isinstance(
            audience_name, str
        ), "`audience_name` should be a non-empty string"
        assert (
            override_type in self.__override_types
        ), f"`override_type` should be in : {self.__override_types}"
        assert (
            isinstance(override_value, str) and override_type != ""
        ), "`override_value` should be non-empty string"
        assert remote_config_name and isinstance(
            audience_name, str
        ), "`remote_config_name` should be a non-empty string"
