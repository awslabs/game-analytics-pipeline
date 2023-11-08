"""
This module contains Application class.
"""
from datetime import datetime
from time import sleep

from typing import Any, List

from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
from mypy_boto3_athena import AthenaClient

from utils import constants


class Application:
    """
    This class represents an analytical application.
    """

    def __init__(
        self,
        athena: AthenaClient,
        application_ID: str,
        application_data: dict[str, Any],
    ):
        self.__athena = athena
        self.__application_ID = application_ID
        self.__data = application_data

    @classmethod
    def from_ID(
        cls,
        database: DynamoDBServiceResource,
        athena: AthenaClient,
        application_ID: str,
    ):
        """
        This method creates an instance of RemoteConfig from ID. It fetches database.
        It returns None if there is no RemoteConfig with this ID.
        """
        response = database.Table(constants.TABLE_APPLICATIONS).get_item(
            Key={"application_id": application_ID}
        )
        if item := response.get("Item"):
            return cls(athena, item.pop("application_id"), item)

    @staticmethod
    def get_all(
        database: DynamoDBServiceResource, athena: AthenaClient
    ) -> List["Application"]:
        """
        This static method returns all applications.
        """
        response = database.Table(constants.TABLE_APPLICATIONS).scan()
        return [
            Application(athena, item.pop("application_id"), item)
            for item in response["Items"]
        ]

    @property
    def application_name(self) -> str:
        """
        This method returns name of application.
        """
        return self.__data["application_name"]

    def get_latest_events(self, limit: int) -> list[dict[str, Any]]:
        """
        This method returns latest events of application.
        """
        now = datetime.now()
        # Start Athena Query
        response = self.__athena.start_query_execution(
            QueryString=f"""
                SELECT *
                FROM {constants.ANALYTICS_TABLE}
                WHERE application_name='{self.application_name}' AND year='{now.year}' AND month='{now.month}' AND day='{now.day}'
                ORDER BY event_timestamp DESC
                LIMIT {limit}
            """,
            QueryExecutionContext={"Database": constants.ANALYTICS_DATABASE},
            ResultConfiguration={
                "OutputLocation": f"s3://{constants.ANALYTICS_BUCKET}/athena_query_results/"
            },
        )
        query_execution_id = response["QueryExecutionId"]
        while True:
            # Wait for the query to be executed
            sleep(0.5)  # To avoid spamming requests
            query_status = self.__athena.get_query_execution(
                QueryExecutionId=query_execution_id
            )["QueryExecution"]["Status"]
            if query_status["State"] not in ("QUEUED", "RUNNING"):
                break

        if query_status == "FAILED":
            raise ValueError(
                f"Error during Athena query execution : {query_status['StateChangeReason']}"
            )

        # Get Athena Query Results
        query_results = self.__athena.get_query_results(
            QueryExecutionId=response["QueryExecutionId"]
        )
        result_set = query_results["ResultSet"]

        # Events Formatting
        columns = [
            column["Label"] for column in result_set["ResultSetMetadata"]["ColumnInfo"]
        ]
        return [
            {
                column: value["VarCharValue"]
                for column, value in zip(columns, row["Data"])
            }
            for row in result_set["Rows"][1:]
        ]

    def to_dict(self) -> dict[str, Any]:
        """
        This method returns a dict that represents the Application.
        """
        return self.__data | {"application_id": self.__application_ID}
