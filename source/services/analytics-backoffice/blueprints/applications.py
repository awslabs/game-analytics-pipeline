"""
This module contains applications endpoints.
"""
from flask import Blueprint, current_app, jsonify, request

from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
from mypy_boto3_athena import AthenaClient

from models.Application import Application


applications_endpoints = Blueprint("applications_endpoints", __name__)


@applications_endpoints.get("/")
def get_applications():
    """
    This endpoint returns applications.
    """
    athena: AthenaClient = current_app.config["athena"]
    database: DynamoDBServiceResource = current_app.config["database"]
    return jsonify(Application.get_all(database, athena))


@applications_endpoints.get("/<application_ID>/events")
def get_events_from_application(application_ID: str):
    """
    This endpoint returns applications.
    """
    athena: AthenaClient = current_app.config["athena"]
    database: DynamoDBServiceResource = current_app.config["database"]


    limit = request.args.get("limit", "50")
    if not limit.isdigit() or int(limit) < 1:
        return jsonify(error="limit should be int and greater than 0"), 400

    if application := Application.from_ID(database, athena, application_ID):
        return jsonify(application.get_latest_events(int(limit)))
    return jsonify(error=f"There is no application with ID : {application_ID}"), 400
