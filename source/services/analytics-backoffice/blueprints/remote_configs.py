"""
This module contains remote_configs endpoints.
"""
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request

from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from models.ABTest import ABTest
from models.RemoteConfig import RemoteConfig


remote_configs_endpoints = Blueprint(
    "remote_configs_endpoints", __name__
)


# @remote_configs_endpoints.get("/")
# def get_all_remote_configs():
#     """
#     This endpoint returns all remote configs.
#     """
#     return jsonify(remote_configs=RemoteConfig.get_all(current_app.config["database"]))


@remote_configs_endpoints.post("/")
def create_remote_config():
    """
    This endpoint allows to create a remote config.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    payload = request.get_json(force=True)

    remote_config_ID = str(uuid4())
    try:
        remote_config = RemoteConfig.from_dict(database, remote_config_ID, payload)
        remote_config.create()
    except AssertionError as e:
        return jsonify(error=str(e)), 400

    return jsonify(remote_config_ID=remote_config_ID), 200


@remote_configs_endpoints.put("/<remote_config_ID>")
def update_remote_config(remote_config_ID: str):
    """
    This endpoint allows to update a remote config.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    payload = request.get_json(force=True)

    remote_config = RemoteConfig.from_id(database, remote_config_ID)
    if not remote_config:
        return (
            jsonify(error=f"There is no remote config with ID : {remote_config_ID}"),
            400,
        )

    try:
        remote_config.update(payload)
    except AssertionError as e:
        return jsonify(error=str(e)), 400

    return jsonify(), 204


@remote_configs_endpoints.delete("/<remote_config_ID>")
def delete_remote_config(remote_config_ID: str):
    """
    This endpoint allows to delete a remote config.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    remote_config = RemoteConfig.from_id(database, remote_config_ID)
    if not remote_config:
        return (
            jsonify(error=f"There is no remote config with id `{remote_config_ID}`"),
            400,
        )
    if remote_config.active:
        return jsonify(error="You can't delete an active remote config"), 400

    remote_config.delete()
    return jsonify(), 204


@remote_configs_endpoints.post("/<remote_config_ID>/activate")
def activate_remote_config(remote_config_ID: str):
    """
    This endpoint allows to activate a remote config.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    remote_config = RemoteConfig.from_id(database, remote_config_ID)
    if not remote_config:
        return (
            jsonify(error=f"There is no remote config with id `{remote_config_ID}`"),
            400,
        )
    remote_config.activate()
    return jsonify(), 204


@remote_configs_endpoints.post(
    "/<remote_config_ID>/condition/<condition_type>"
)
def set_condition(remote_config_ID: str, condition_type: str):
    """
    This endpoint allows to set remote config condition.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    payload = request.get_json(force=True)

    remote_config = RemoteConfig.from_id(database, remote_config_ID)
    if not remote_config:
        return (
            jsonify(error=f"There is no remote config with id `{remote_config_ID}`"),
            400,
        )

    try:
        remote_config.set_condition(condition_type, payload["condition_value"])
    except (AssertionError, KeyError) as e:
        return jsonify(error=str(e)), 400

    return jsonify(), 204


@remote_configs_endpoints.delete(
    "/<remote_config_ID>/condition/<condition_type>"
)
def delete_condition(remote_config_ID: str, condition_type: str):
    """
    This endpoint allows to delete remote config condition.
    """
    database: DynamoDBServiceResource = current_app.config["database"]

    remote_config = RemoteConfig.from_id(database, remote_config_ID)
    if not remote_config:
        return (
            jsonify(error=f"There is no remote config with id `{remote_config_ID}`"),
            400,
        )

    try:
        remote_config.delete_condition(condition_type)
    except AssertionError as e:
        return jsonify(error=str(e)), 400
    return jsonify(), 204


@remote_configs_endpoints.post("/<remote_config_ID>/abtest")
def create_abtest(remote_config_ID: str):
    """
    This endpoint allows to create an abtest from a remote config.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    payload = request.get_json(force=True)

    remote_config = RemoteConfig.from_id(database, remote_config_ID)

    if not remote_config:
        return (
            jsonify(error=f"There is no remote config with id `{remote_config_ID}`"),
            400,
        )

    abtest_ID = str(uuid4())

    try:
        remote_config.create_abtest(abtest_ID, payload)
    except AssertionError as e:
        return jsonify(error=str(e)), 400
    except KeyError as e:
        return jsonify(error=f"missing {e}"), 400

    return jsonify(abtest_ID=abtest_ID)


@remote_configs_endpoints.put("/abtests/<abtest_ID>")
def update_abtest(abtest_ID: str):
    """
    This endpoint allows to update an abtest.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    payload = request.get_json(force=True)

    remote_config = RemoteConfig.from_abtest_id(database, abtest_ID)

    if not remote_config:
        return jsonify(error=f"There is no ABTest with id `{abtest_ID}`"), 400

    try:
        remote_config.update_abtest(abtest_ID, payload)
    except AssertionError as e:
        return jsonify(error=str(e)), 400
    except KeyError as e:
        return jsonify(error=f"missing {e}"), 400

    return jsonify(), 204


@remote_configs_endpoints.delete("/abtests/<abtest_ID>")
def delete_abtest(abtest_ID: str):
    """
    This endpoint allows to delete an abtest.
    """
    database: DynamoDBServiceResource = current_app.config["database"]

    remote_config = RemoteConfig.from_abtest_id(database, abtest_ID)

    if not remote_config:
        return jsonify(error=f"There is no ABTest with id `{abtest_ID}`"), 400

    try:
        remote_config.delete_abtest(abtest_ID)
    except AssertionError as e:
        return jsonify(error=str(e)), 400

    return jsonify(), 204


@remote_configs_endpoints.post("/abtests/<abtest_ID>/activate")
def activate_abtest(abtest_ID: str):
    """
    This endpoint allows to activate an abtest.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    payload = request.get_json(force=True)

    remote_config = RemoteConfig.from_abtest_id(database, abtest_ID)

    active_abtests = ABTest.get_actives(database)
    if not remote_config:
        return jsonify(error=f"There is no ABTest with id `{abtest_ID}`"), 400
    if not remote_config.active:
        return (
            jsonify(error="You can't activate an ABTest on deactivate remote config"),
            400,
        )
    if remote_config.has_active_abtest(active_abtests):
        return (
            jsonify(error="There is already an active abtest on this remote config"),
            400,
        )

    try:
        remote_config.activate_abtest(abtest_ID, payload.get("start_timestamp"))
    except AssertionError as e:
        return jsonify(error=str(e)), 400

    return jsonify(), 204


@remote_configs_endpoints.post("/abtests/<abtest_ID>/pause")
def pause_abtest(abtest_ID: str):
    """
    This endpoint allows to pause an abtest.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    payload = request.get_json(force=True)

    remote_config = RemoteConfig.from_abtest_id(database, abtest_ID)

    if not remote_config:
        return jsonify(error=f"There is no ABTest with id `{abtest_ID}`"), 400

    if not isinstance(payload.get("paused"), bool):
        return jsonify(error="`paused` should be boolean"), 400

    try:
        remote_config.pause_abtest(abtest_ID, payload["paused"])
    except AssertionError as e:
        return jsonify(error=str(e)), 400

    return jsonify(), 204


@remote_configs_endpoints.post("/abtests/<abtest_ID>/promote")
def promote_abtest(abtest_ID: str):
    """
    This endpoint allows to promote an abtest.
    """
    database: DynamoDBServiceResource = current_app.config["database"]
    payload = request.get_json(force=True)

    remote_config = RemoteConfig.from_abtest_id(database, abtest_ID)

    if not remote_config:
        return jsonify(error=f"There is no ABTest with id `{abtest_ID}`"), 400

    if not isinstance(payload.get("reference_value"), str):
        return jsonify(error="`reference_value` should be str"), 400

    try:
        remote_config.promote_abtest(abtest_ID, payload["reference_value"])
    except AssertionError as e:
        return jsonify(error=str(e)), 400

    return jsonify(), 204
