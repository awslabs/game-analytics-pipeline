"""
This module contains ABTest class.
"""
from decimal import Decimal
from time import time
from typing import Any, List

from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from utils import constants


class ABTest:
    """
    This class represents an ABTest.
    """

    def __init__(
        self,
        database: DynamoDBServiceResource,
        abtest_ID: str,
        abtest_data: dict[str, Any],
    ):
        self.__database = database
        self.__abtest_ID = abtest_ID
        self.__data = abtest_data

    @classmethod
    def from_dict(
        cls,
        database: DynamoDBServiceResource,
        abtest_ID: str,
        abtest_data: dict[str, Any],
    ):
        """
        This method creates an instance of ABTest from dict.
        It raises AssertionError if abtest_data not matches with ABTest schema.
        """
        cls.__assert_data(abtest_data)
        return cls(database, abtest_ID, abtest_data)

    @classmethod
    def from_id(cls, database: DynamoDBServiceResource, abtest_ID: str):
        """
        This method creates an instance of ABTest from ID. It fetches database.
        It returns None if there is no ABTest with this ID.
        """
        response = database.Table(constants.TABLE_ABTESTS).get_item(
            Key={"ID": abtest_ID}
        )
        if item := response.get("Item"):
            return cls(database, item.pop("ID"), item)

    @staticmethod
    def get_actives(database: DynamoDBServiceResource) -> List["ABTest"]:
        """
        This method returns a list of all actives ABTests.
        """
        response = database.Table(constants.TABLE_ABTESTS).query(
            IndexName="active-index", KeyConditionExpression=Key("active").eq(1)
        )
        return [ABTest(database, item.pop("ID"), item) for item in response["Items"]]

    @property
    def active(self) -> bool:
        """
        This method return True if ABTest is active, else False.
        """
        return self.__data["active"]

    @property
    def id(self) -> str:
        """
        This method return id of ABTest.
        """
        return self.__abtest_ID

    @property
    def name(self) -> str:
        """
        This method returns name.
        """
        return self.__data["name"]

    @property
    def paused(self) -> bool:
        """
        This method returns paused.
        """
        return self.__data["paused"]

    @property
    def pauses(self) -> list[dict[str, int]]:
        """
        This method returns pauses.
        """
        return self.__data["pauses"]

    @property
    def remote_config_ID(self) -> str:
        """
        This method returns remote_config_ID.
        """
        return self.__data["remote_config_ID"]

    @property
    def start_timestamp(self) -> int:
        """
        This method returns start_timestamp.
        """
        return self.__data["start_timestamp"]

    @property
    def target_user_percent(self) -> int:
        """
        This method returns target_user_percent.
        """
        return self.__data["target_user_percent"]

    @property
    def variants(self) -> list[str]:
        """
        This method returns variants.
        """
        return self.__data["variants"]

    def activate(self, start_timestamp: int | None = None):
        """
        This method activates ABTest in database.
        It raises AssertionError if start_timestamp is less than the current timestamp.
        """
        now = int(time())
        if start_timestamp:
            assert (
                start_timestamp > now
            ), "The `start_timestamp` should be greater than the current timestamp"

        self.__database.Table(constants.TABLE_ABTESTS).update_item(
            Key={"ID": self.__abtest_ID},
            AttributeUpdates={
                "active": {"Value": 1, "Action": "PUT"},
                "start_timestamp": {"Value": now, "Action": "PUT"},
            },
        )

    def create(self, remote_config_ID: str):
        """
        This method creates an ABTest in database.
        """
        response = self.__database.Table(constants.TABLE_ABTESTS).query(
            IndexName="remote_config_ID-name-index",
            KeyConditionExpression=Key("remote_config_ID").eq(remote_config_ID)
            & Key("name").eq(self.name),
        )
        if response.get("Items"):
            raise AssertionError(
                f"There is already an ABTest named {self.name} on remote_config {remote_config_ID}"
            )

        self.__database.Table(constants.TABLE_ABTESTS).put_item(
            Item=self.__data
            | {
                "ID": self.__abtest_ID,
                "paused": False,
                "pauses": [],
                "remote_config_ID": remote_config_ID,
                "active": 0,
            }
        )

    def delete(self):
        """
        This method deletes an ABTest from database.
        """
        self.__database.Table(constants.TABLE_ABTESTS).delete_item(
            Key={"ID": self.__abtest_ID}
        )

    def pause(self, paused: bool):
        """
        This method pauses ABTest in database.
        It raises AssertionError if ABTest is NOT active.
        """
        if not self.active:
            raise AssertionError("You cannot pause an active ABTest")

        if self.paused == paused:
            raise AssertionError(
                f"This abtest has already paused field set to {paused}"
            )

        now = int(time())
        pauses = self.pauses
        if paused:
            pauses.append({"start_timestamp": now})
        else:
            pauses[-1]["end_timestamp"] = now

        self.__database.Table(constants.TABLE_ABTESTS).update_item(
            Key={"ID": self.__abtest_ID},
            AttributeUpdates={
                "paused": {"Value": paused, "Action": "PUT"},
                "pauses": {"Value": pauses, "Action": "PUT"},
            },
        )

    def purge(self):
        """
        This method deletes all UserABTests link to this ABTest.
        Batch Writer Documentation : https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/batch_writer.html
        """
        table = self.__database.Table(constants.TABLE_USERS_ABTESTS)
        response = table.query(
            IndexName="abtest_ID-index",
            KeyConditionExpression=Key("abtest_ID").eq(self.__abtest_ID),
        )

        with table.batch_writer() as batch:
            for item in response["Items"]:
                batch.delete_item(
                    Key={"uid": item["uid"], "abtest_ID": item["abtest_ID"]}
                )

    def save_history(
        self, remote_config_name: str, reference_value: str, promoted_value: str
    ):
        """
        This method saves ABTest in history.
        """
        now = int(time())
        pauses = self.pauses
        if self.pauses and not pauses[-1].get("end_timestamp"):
            # Missing end_timestamp field because user has promote paused ABTest.
            pauses[-1]["end_timestamp"] = int(time())

        self.__database.Table(constants.TABLE_ABTESTS_HISTORY).put_item(
            Item={
                "abtest_ID": self.__abtest_ID,
                "abtest_name": self.name,
                "end_timestamp": now,
                "pauses": pauses,
                "promoted_value": promoted_value,
                "reference_value": reference_value,
                "remote_config_name": remote_config_name,
                "start_timestamp": self.start_timestamp,
                "target_user_percent": self.target_user_percent,
                "variants": self.variants,
            }
        )

    def update(self, new_data: dict[str, Any]):
        """
        This method updates ABTest in database.
        It raises AssertionError if new_data not matches with ABTest schema.
        """
        self.__assert_data(new_data)

        self.__database.Table(constants.TABLE_ABTESTS).update_item(
            Key={"ID": self.__abtest_ID},
            AttributeUpdates={
                key: {"Value": value, "Action": "PUT"}
                for key, value in new_data.items()
            },
        )

    def to_dict(self) -> dict[str, Any]:
        """
        This method returns a dict that represents the ABTest.
        """
        return self.__data

    @staticmethod
    def __assert_data(data: dict[str, Any]):
        copy_data = data.copy()
        assert isinstance(copy_data.pop("name"), str), "`name should be str`"
        assert isinstance(
            copy_data["target_user_percent"], (int, Decimal)
        ), "`target_user_percent` should be int"
        assert (
            0 <= copy_data.pop("target_user_percent") <= 100
        ), "`target_user_percent` should match with 0 <= {value} <= 100"
        assert isinstance(
            copy_data.pop("variants"), list
        ), "`variants` should be array of str"

        if copy_data:
            raise AssertionError(f"Unexpected fields : {list(copy_data)}")
