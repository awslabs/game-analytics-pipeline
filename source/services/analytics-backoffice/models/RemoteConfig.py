"""
This module contains RemoteConfig class.
"""
from decimal import Decimal
from typing import Any

from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from models.ABTest import ABTest
from utils import constants


class RemoteConfig:
    """
    This class represents a mobile application configuration that we can manage remotely.
    """

    def __init__(
        self,
        database: DynamoDBServiceResource,
        remote_config_ID: str,
        remote_config_data: dict[str, Any],
    ):
        self.__database = database
        self.__remote_config_ID = remote_config_ID
        self.__data = remote_config_data

    @classmethod
    def from_abtest_id(cls, database: DynamoDBServiceResource, abtest_ID: str):
        """
        This method creates an instance of RemoteConfig from abtest_ID. it fetches database.
        It returns None if there is no ABTest with this ID.
        """
        if abtest := ABTest.from_id(database, abtest_ID):
            return cls.from_id(database, abtest.remote_config_ID)

    @classmethod
    def from_dict(
        cls,
        database: DynamoDBServiceResource,
        remote_config_ID: str,
        remote_config_data: dict[str, Any],
    ):
        """
        This method creates an instance of RemoteConfig from dict.
        It raises AssertionError if remote_config_data not matches with RemoteConfig schema.
        """
        cls.__assert_data(remote_config_data)
        return cls(database, remote_config_ID, remote_config_data)

    @classmethod
    def from_id(cls, database: DynamoDBServiceResource, remote_config_ID: str):
        """
        This method creates an instance of RemoteConfig from ID. It fetches database.
        It returns None if there is no RemoteConfig with this ID.
        """
        response = database.Table(constants.TABLE_REMOTE_CONFIGS).get_item(
            Key={"ID": remote_config_ID}
        )
        if item := response.get("Item"):
            return cls(database, item.pop("ID"), item)

    @property
    def active(self) -> bool:
        """
        This method returns True if RemoteConfig is active, else False.
        """
        return self.__data["active"] == 1

    @property
    def id(self) -> str:
        """
        This method returns id of RemoteConfig.
        """
        return self.__remote_config_ID

    @property
    def name(self) -> str:
        """
        This method returns name.
        """
        return self.__data["name"]

    @property
    def reference_value(self) -> str:
        """
        This method returns reference_value.
        """
        return self.__data["reference_value"]

    def activate(self):
        """
        This method activates RemoteConfig in database.
        """
        self.__database.Table(constants.TABLE_REMOTE_CONFIGS).update_item(
            Key={"ID": self.__remote_config_ID},
            AttributeUpdates={"active": {"Value": 1, "Action": "PUT"}},
        )

    def activate_abtest(self, abtest_ID: str, start_timestamp: int | None = None):
        """
        This method activates ABTest in database.
        It raises AssertionError if start_timestamp is less than the current timestamp.
        """
        if abtest := ABTest.from_id(self.__database, abtest_ID):
            abtest.activate(start_timestamp)

    def create(self):
        """
        This method creates RemoteConfig in database.
        """
        # Check if there is already a remote config with the same name
        if self.__name_exists(self.name):
            raise AssertionError(f"There is already a remote config named {self.name}")

        self.__database.Table(constants.TABLE_REMOTE_CONFIGS).put_item(
            Item=self.__data | {"ID": self.__remote_config_ID, "active": 0}
        )

    def create_abtest(self, abtest_ID: str, abtest_data: dict[str, Any]):
        """
        This method creates an ABTest for this RemoteConfig.
        It raises AssertionError if abtest_data not matches with ABTest schema.
        """
        abtest = ABTest.from_dict(self.__database, abtest_ID, abtest_data)
        abtest.create(self.__remote_config_ID)

    def delete(self):
        """
        This method deletes RemoteConfig from database.
        """
        self.__database.Table(constants.TABLE_REMOTE_CONFIGS).delete_item(
            Key={"ID": self.__remote_config_ID}
        )

    def delete_abtest(self, abtest_ID: str):
        """
        This method deletes an ABTest. It returns None if there is no ABTest with this ID.
        """
        if abtest := ABTest.from_id(self.__database, abtest_ID):
            if abtest.active:
                raise AssertionError("You can't update an activated ABTest")
            abtest.delete()

    def delete_condition(self, condition_type: str):
        """
        This method deletes condition for this RemoteConfig.
        It raises AssertionError if condition_type is not allowed.
        """
        if condition_type not in constants.ALLOWED_REMOTE_CONFIGS_CONDITIONS:
            raise AssertionError(f"condition_type {condition_type} not allowed")

        self.__database.Table(constants.TABLE_REMOTE_CONFIGS_CONDITIONS).delete_item(
            Key={
                "remote_config_ID": self.__remote_config_ID,
                "condition_type": condition_type,
            }
        )

    def has_active_abtest(self, active_abtests: list[ABTest]) -> bool:
        """
        This method returns True if this RemoteConfig
        has already an active abtest, else False.
        """
        return any(
            abtest.remote_config_ID == self.__remote_config_ID
            for abtest in active_abtests
        )

    def pause_abtest(self, abtest_ID: str, paused: bool):
        """
        This method pauses ABTest in database.
        It raises AssertionError if ABTest is NOT active.
        """
        if abtest := ABTest.from_id(self.__database, abtest_ID):
            abtest.pause(paused)

    def promote_abtest(self, abtest_ID: str, promoted_value: str):
        """
        This method promotes ABTest in database.
        It raises AssertionError if ABTest is NOT active
        or if promoted_value is NOT in ABTest.
        """
        abtest = ABTest.from_id(self.__database, abtest_ID)
        if not abtest:
            return

        if not abtest.active:
            raise AssertionError("You can't promote a deactivated ABTest")

        if promoted_value not in [self.reference_value] + abtest.variants:
            raise AssertionError(f"{promoted_value} value not in ABTest {abtest_ID}")

        # Update reference value of remote config
        self.__database.Table(constants.TABLE_REMOTE_CONFIGS).update_item(
            Key={"ID": self.__remote_config_ID},
            AttributeUpdates={
                "reference_value": {"Value": promoted_value, "Action": "PUT"}
            },
        )

        abtest.save_history(self.name, self.reference_value, promoted_value)
        abtest.purge()
        abtest.delete()

    def set_condition(self, condition_type: str, condition_value: Any):
        """
        This method sets a condition for this RemoteConfig.
        It raises AssertionError if condition_type is not allowed.
        """
        if condition_type not in constants.ALLOWED_REMOTE_CONFIGS_CONDITIONS:
            raise AssertionError(f"condition_type {condition_type} not allowed")

        if isinstance(condition_value, (float, int)):
            condition_value = Decimal(condition_value)

        self.__database.Table(constants.TABLE_REMOTE_CONFIGS_CONDITIONS).put_item(
            Item={
                "remote_config_ID": self.__remote_config_ID,
                "condition_type": condition_type,
                "condition_value": condition_value,
            }
        )

    def update(self, new_data: dict[str, Any]):
        """
        This method updates RemoteConfig in database.
        It raises AssertionError if new_data not matches with RemoteConfig schema.
        """
        self.__assert_data(new_data)
        new_name = new_data["name"]

        if self.active:
            # These fields can't updated if RemoteConfig is active
            assert (
                self.name == new_name
            ), "You can't update `name` field because remote config is active"
            assert (
                self.reference_value == new_data["reference_value"]
            ), "You can't update `reference_value` field because remote config is active"

        if self.__name_exists(new_name, to_exclude=self.__remote_config_ID):
            raise AssertionError(f"There is already a remote config named {new_name}")

        self.__database.Table(constants.TABLE_REMOTE_CONFIGS).update_item(
            Key={"ID": self.__remote_config_ID},
            AttributeUpdates={
                key: {"Value": value, "Action": "PUT"}
                for key, value in new_data.items()
            },
        )

    def update_abtest(self, abtest_ID: str, new_abtest_data: dict[str, Any]):
        """
        This method updates an ABTest. It returns None if there is no ABTest with this ID.
        It raises AssertionError if abtest_data not matches with ABTest schema.
        """
        if abtest := ABTest.from_id(self.__database, abtest_ID):
            if abtest.active:
                raise AssertionError("You can't update an activated ABTest")
            abtest.update(new_abtest_data)

    @staticmethod
    def __assert_data(data: dict[str, Any]):
        copy_data = data.copy()
        assert isinstance(
            copy_data.pop("description", None), str
        ), "`description` should be str"
        assert isinstance(copy_data.pop("name", None), str), "`name` should be str"
        assert isinstance(
            copy_data.pop("reference_value", None), str
        ), "`reference_value` should be str"

        if copy_data:
            raise AssertionError(f"Unexpected fields : {list(copy_data)}")

    def __name_exists(self, name: str, to_exclude: str = "") -> bool:
        response = self.__database.Table(constants.TABLE_REMOTE_CONFIGS).query(
            IndexName="name-index",
            KeyConditionExpression=Key("name").eq(name),
        )
        return any(item["ID"] != to_exclude for item in response.get("Items", []))
