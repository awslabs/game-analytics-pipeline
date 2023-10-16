"""
This module contains main endpoints of analytics backoffice API.
"""
import contextlib
from decimal import Decimal

import boto3
from flask import Blueprint, Flask, jsonify
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS

from blueprints.applications import applications_endpoints
from blueprints.remote_configs import remote_configs_endpoints


class FlaskAppEncoder(DefaultJSONProvider):
    """
    Custom JSONEncoder for Flask app. For example, It uses with jsonify() method
    """

    def default(self, o):
        """default"""
        if isinstance(o, Decimal):
            to_int = int(o)
            to_float = float(o)
            return to_int if to_int == to_float else to_float

        with contextlib.suppress(AttributeError):
            return o.to_dict()

        return super().default(o)


app = Flask(__name__)
app.json_provider_class = FlaskAppEncoder
app.json = FlaskAppEncoder(app)
CORS(app)

app.config["athena"] = boto3.client("athena")
app.config["database"] = boto3.resource("dynamodb")

# Use base Blueprint to link with AWS custom domain
main_blueprint = Blueprint("analytics-backoffice", __name__)

main_blueprint.register_blueprint(applications_endpoints, url_prefix="/applications")
main_blueprint.register_blueprint(
    remote_configs_endpoints, url_prefix="/remote-configs"
)


@main_blueprint.get("/")
def default():
    """
    Default endpoint.
    """
    return jsonify(), 204


app.register_blueprint(main_blueprint, url_prefix="/analytics-backoffice")


if __name__ == "__main__":
    # Used when running locally.
    app.run(host="localhost", port=8080, debug=True)
