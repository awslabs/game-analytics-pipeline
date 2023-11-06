"""
This module contains audiences endpoints.
"""
from flask import Blueprint, current_app, jsonify, request

from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from models.Audience import Audience
from models.RemoteConfigOverride import RemoteConfigOverride


audiences_endpoints = Blueprint("audiences_endpoints", __name__)


@audiences_endpoints.get("/")
def get_audiences():
    """
    This endpoint returns all audiences.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    return jsonify(Audience.get_all(database))


@audiences_endpoints.post("/<audience_name>")
def set_audience(audience_name: str):
    """
    This endpoint sets an audience.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    payload = request.get_json(force=True) | {"audience_name": audience_name}

    try:
        audience = Audience(database, payload)
    except AssertionError as e:
        return jsonify(error=str(e)), 400
    except KeyError as e:
        return jsonify(error=f"Invalid payload : missing {e}"), 400

    audience.update_database()
    return jsonify(), 204


@audiences_endpoints.delete("/<audience_name>")
def delete_audience(audience_name: str):
    """
    This endpoint deletes an audience.
    """
    database: DynamoDBServiceResource = current_app.config["database"]

    audience = Audience.from_database(database, audience_name)
    if not audience:
        return (
            jsonify(error=f"There is no audience with {audience_name} audience_name"),
            400,
        )

    remote_configs_overrides = RemoteConfigOverride.from_audience_name(
        database, audience_name
    )
    if len(remote_configs_overrides) > 0:
        return (
            jsonify(
                error="You can NOT delete audience : it used in Remote Config Overrides"
            ),
            400,
        )

    audience.delete()
    return jsonify(), 204
