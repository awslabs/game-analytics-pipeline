"""
This module contains abtests endpoints.
"""
from flask import Blueprint, current_app, jsonify

from models.RemoteConfig import RemoteConfig


remote_configs_endpoints = Blueprint("remote_configs_endpoints", __name__)


@remote_configs_endpoints.get("/<uid>")
def get_uid_slot(uid: str):
    """
    This endpoint returns all remote configs.
    """
    remote_configs = RemoteConfig.get_all_from_uid(current_app.config["database"], uid)
    return jsonify(remote_configs=remote_configs)
