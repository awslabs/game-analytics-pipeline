"""
This module contains abtests endpoints.
"""
from flask import Blueprint, current_app, jsonify, request

from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from models.ABTest import ABTest
from models.RemoteConfigOverride import RemoteConfigOverride


abtests_endpoints = Blueprint("abtests_endpoints", __name__)


@abtests_endpoints.get("/")
def get_abtests():
    """
    This endpoint returns all abtests.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    return jsonify(ABTest.get_all(database))


@abtests_endpoints.post("/<abtest_name>")
def set_abtest(abtest_name: str):
    """
    This endpoint sets an abtest.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    payload = request.get_json(force=True) | {"abtest_name": abtest_name}

    try:
        abtest = ABTest(database, payload)
    except AssertionError as e:
        return jsonify(error=str(e)), 400
    except KeyError as e:
        return jsonify(error=f"Invalid payload : missing {e}"), 400

    abtest.update_database()
    return jsonify(), 204


@abtests_endpoints.delete("/<abtest_name>")
def delete_abtest(abtest_name: str):
    """
    This endpoint deletes an abtest.
    """
    database: DynamoDBServiceResource = current_app.config["database"]

    abtest = ABTest.from_name(database, abtest_name)
    if not abtest:
        return jsonify(error=f"There is no abtest with {abtest_name} name"), 400

    remote_configs_overrides = RemoteConfigOverride.from_abtest_name(
        database, abtest_name
    )
    if len(remote_configs_overrides) > 0:
        return jsonify(error="You can NOT remove used abtest"), 400

    abtest.delete()
    return jsonify(), 204


@abtests_endpoints.post("/<abtest_name>/promote")
def promote_abtest(abtest_name: str):
    """
    This endpoint promotes an abtest.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    payload = request.get_json(force=True)

    abtest = ABTest.from_name(database, abtest_name)
    if not abtest:
        return jsonify(error=f"There is no abtest with {abtest_name} name"), 400

    try:
        remote_config_name = payload["remote_config_name"]
        audience_name = payload["audience_name"]
        promoted_value = payload["promoted_value"]
    except KeyError as e:
        return jsonify(error=f"Invalid paylaod : missing {e}"), 400

    if promoted_value not in abtest.variants:
        return jsonify(error=f"`promoted_value` not in {abtest.variants}"), 400

    # Update override value
    override = RemoteConfigOverride.from_database(
        database, remote_config_name, audience_name
    )
    if not override:
        return (
            jsonify(
                error=f"There is not remote config override with {remote_config_name} remote_config_name and {audience_name} audience_name."
            ),
            400,
        )

    if override.override_type != "abtest":
        return jsonify(error="This override is NOT an abtest"), 400

    override.fix_value(promoted_value, abtest)

    abtest.purge()
    abtest.delete()

    return jsonify(), 204
