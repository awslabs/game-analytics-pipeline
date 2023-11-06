"""
This module contains remote_configs endpoints.
"""
from flask import Blueprint, current_app, jsonify, request

from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from models.ABTest import ABTest
from models.Audience import Audience
from models.RemoteConfig import RemoteConfig
from models.RemoteConfigOverride import RemoteConfigOverride


remote_configs_endpoints = Blueprint("remote_configs_endpoints", __name__)


@remote_configs_endpoints.get("/")
def get_remote_configs():
    """
    This endpoint returns all remote configs.
    """
    return jsonify(remote_configs=RemoteConfig.get_all(current_app.config["database"]))


@remote_configs_endpoints.post("/<remote_config_name>")
def set_remote_config(remote_config_name: str):
    """
    This endpoint sets a remote config.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    payload = request.get_json(force=True) | {"remote_config_name": remote_config_name}

    try:
        remote_config = RemoteConfig(database, payload)
    except KeyError as e:
        return jsonify(error=f"Invalid payload : missing {e}"), 400
    except AssertionError as e:
        return jsonify(error=str(e)), 400

    remote_config.update_database()
    return jsonify(), 204


@remote_configs_endpoints.post("/<remote_config_name>/override/<audience_name>")
def set_remote_config_override(remote_config_name: str, audience_name: str):
    """
    This endpoint sets override for a remote config.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    payload = request.get_json(force=True) | {
        "remote_config_name": remote_config_name,
        "audience_name": audience_name,
    }

    if not RemoteConfig.exists(database, remote_config_name):
        return (
            jsonify(error=f"There is no remote config with name {remote_config_name}"),
            400,
        )

    if not Audience.exists(database, audience_name):
        return jsonify(error=f"There is no audience with name {audience_name}"), 400

    try:
        override = RemoteConfigOverride(database, payload)
    except AssertionError as e:
        return jsonify(error=str(e)), 400
    except KeyError as e:
        return jsonify(error=f"Invalid payload : missing {e}"), 400

    if override.activated:
        return jsonify(error="You can NOT update activated remote config override"), 400

    if override.override_type == "abtest":
        if not ABTest.exists(database, override.override_value):
            return (
                jsonify(
                    error=f"There is no ABTest with name {override.override_value}"
                ),
                400,
            )

        remote_configs_overrides = RemoteConfigOverride.from_abtest_name(
            database, override.override_value, exclude=override
        )

        if len(remote_configs_overrides) > 0:
            return (
                jsonify(
                    error=f"ABTest {override.override_value} is already linked to a remote config override"
                ),
                400,
            )

    override.update_database()
    return jsonify(), 204


@remote_configs_endpoints.delete("/<remote_config_name>/override/<audience_name>")
def delete_remote_config_override(remote_config_name: str, audience_name: str):
    """
    This endpoint deletes override for a remote config.
    """
    database: DynamoDBServiceResource = current_app.config["database"]

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

    if override.activated:
        return jsonify(error="You can NOT delete activated remote config override"), 400

    override.delete()
    return jsonify(), 204


@remote_configs_endpoints.post(
    "/<remote_config_name>/override/<audience_name>/activate"
)
def activate_remote_config_override(remote_config_name: str, audience_name: str):
    """
    This endpoint activates/deactivates override for a remote config.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    payload = request.get_json(force=True)

    try:
        activated = payload["activated"]
        assert isinstance(activated, bool), "`activated` should be boolean"
    except AssertionError as e:
        return jsonify(error=str(e)), 400
    except KeyError as e:
        return jsonify(error=f"Invalid payload : missing {e}"), 400

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

    if override.activated == activated:
        return (
            jsonify(
                error=f"Remote config override has already activated field set to {activated}"
            ),
            400,
        )

    if override.override_type == "abtest" and not activated:
        return (
            jsonify(
                error="You can NOT deactivate an abtest override, you should promote abtest."
            ),
            400,
        )

    override.activate(activated)
    return jsonify(), 204
