"""
This module contains RemoteConfig class.
"""
from collections import defaultdict
from typing import Any

from boto3.dynamodb.conditions import Attr, Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from models.ABTest import ABTest
from models.UserABTest import UserABTest
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

    @staticmethod
    def get_all_from_uid(
        database: DynamoDBServiceResource, uid: str, application_ID: str
    ) -> list[dict[str, str]]:
        """
        This method returns a list of all remote configs from an uid.
        If a remote config has an active ABTest, we retrieve his group, or set the user to a group if it has none.
        """
        response = database.Table(constants.TABLE_REMOTE_CONFIGS).query(
            IndexName="application_ID-active-index",
            KeyConditionExpression=Key("application_ID").eq(application_ID) & Key("active").eq(1)
        )

        remote_configs = []
        for remote_config_data in response["Items"]:
            remote_config = RemoteConfig(
                database, remote_config_data.pop("ID"), remote_config_data
            )
            abtest = ABTest.active_from_remote_config_id(database, remote_config.id)
            remote_configs.append(remote_config.to_user_remote_config(uid, abtest))

        return remote_configs

    @property
    def active(self) -> bool:
        """
        This method returns True if RemoteConfig is active, else False.
        """
        return self.__data["active"] == 1

    @property
    def application_ID(self) -> str:
        """
        This method returns application_ID.
        """
        return self.__data["application_ID"]

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

    def activate_abtest(self, abtest_ID: str, start_timestamp: str | None = None):
        """
        This method activates ABTest in database.
        It raises AssertionError if start_timestamp is less than the current timestamp.
        """
        if abtest := ABTest.from_id(self.__database, abtest_ID):
            abtest.activate(start_timestamp)

    def create(self, application_ID: str):
        """
        This method creates RemoteConfig in database.
        """
        assert isinstance(application_ID, str), "`application_ID` should be str"

        # Check if there is already a remote config with the same name and same application_ID
        if self.__name_exists(self.name, application_ID):
            raise AssertionError(
                f"There is already a remote config named {self.name} on app {application_ID}"
            )

        self.__database.Table(constants.TABLE_REMOTE_CONFIGS).put_item(
            Item=self.__data
            | {"ID": self.__remote_config_ID, "active": 0, "application_ID": application_ID}
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

    def has_active_abtest(self, active_abtests: list[ABTest]) -> bool:
        """
        This method returns True if this RemoteConfig
        has already an active abtest, else False.
        """
        return any(
            abtest.remote_config_ID == self.__remote_config_ID
            for abtest in active_abtests
        )

    def max_active_abtests(self, active_abtests: list[ABTest]) -> bool:
        """
        This method returns True if this RemoteConfig
        has already the maximum number of activated abtest.
        """
        # remote_configs = {<remote_config_ID> : list[ABTest]}
        remote_configs = defaultdict(list)
        for abtest in active_abtests:
            remote_configs[abtest.remote_config_ID].append(abtest)

        if len(remote_configs) < constants.MAX_ACTIVATED_ABTESTS:
            return False

        # Retrieve all RemoteConfig that have same application_ID and remote_config_ID
        # equal to at least one of the active abstests
        response = self.__database.Table(constants.TABLE_REMOTE_CONFIGS).query(
            IndexName="application_ID-index",
            KeyConditionExpression=Key("application_ID").eq(self.application_ID),
            FilterExpression=Attr("ID").is_in(list(remote_configs)),
        )

        return (
            sum(
                len(remote_configs[item["remote_config_ID"]])
                for item in response["Items"]
            )
            >= constants.MAX_ACTIVATED_ABTESTS
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

        abtest.save_history(
            self.application_ID, self.name, self.reference_value, promoted_value
        )
        abtest.purge()
        abtest.delete()

    def to_user_remote_config(self, uid: str, abtest: ABTest | None = None) -> dict[str, str]:
        """
        This method returns a dict that represents the remote config with user specifications.
        It assigns user to a group of the ABTest if he has not been assigned.
        """
        value_origin = "reference_value"
        value = self.reference_value

        if abtest:
            # There is an active ABTest
            user_abtest = UserABTest(self.__database, uid, abtest.id)
            if not user_abtest.has_group:
                # We set user to a group
                user_abtest.set_group(
                    abtest.target_user_percent,
                    self.__data["reference_value"],
                    abtest.variants,
                )
            value_origin = "abtest" if user_abtest.is_in_test else "reference_value"
            value = user_abtest.value

        return {
            "name": self.name,
            "value_origin": value_origin,
            "value": value,
        }

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

        if self.__name_exists(
            new_name, self.application_ID, to_exclude=self.__remote_config_ID
        ):
            raise AssertionError(
                f"There is already a remote config named {new_name} on app {self.application_ID}"
            )

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

    def __name_exists(self, name: str, application_ID: str, to_exclude: str = "") -> bool:
        response = self.__database.Table(constants.TABLE_REMOTE_CONFIGS).query(
            IndexName="application_ID-name-index",
            KeyConditionExpression=Key("application_ID").eq(application_ID)
            & Key("name").eq(name),
        )
        return any(item["ID"] != to_exclude for item in response.get("Items", []))
