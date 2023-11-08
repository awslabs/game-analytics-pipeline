"""
This module contains ABTest class.
"""
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from utils import constants


class ABTest:
    """
    This class represents an ABTest.
    """

    def __init__(self, dynamodb: DynamoDBServiceResource, abtest_name: str):
        response = dynamodb.Table(constants.ABTESTS_TABLE).get_item(
            Key={"abtest_name": abtest_name}
        )
        self.__data = response["Item"]

    @property
    def abtest_name(self) -> str:
        """
        This property returns abtest_name.
        """
        return self.__data["abtest_name"]

    @property
    def target_user_percent(self) -> int:
        """
        This property returns target_user_percent.
        """
        return self.__data["target_user_percent"]

    @property
    def variants(self) -> list[str]:
        """
        This property returns variants.
        """
        return self.__data["variants"]
