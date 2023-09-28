"""
This module contains main endpoints.
"""
import contextlib
from decimal import Decimal

import boto3
from flask import Flask, jsonify
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS

from blueprints.backoffice_remote_configs import backoffice_remote_configs_endpoints
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

app.register_blueprint(
    backoffice_remote_configs_endpoints, url_prefix="/backoffice/remote-configs"
)
app.register_blueprint(remote_configs_endpoints, url_prefix="/remote-configs")

app.config["database"] = boto3.resource("dynamodb")
app.config["secrets_manager"] = boto3.client("secretsmanager")


@app.get("/")
def default():
    """
    Default endpoint.
    """
    return jsonify(), 204


if __name__ == "__main__":
    # Used when running locally.
    app.run(host="localhost", port=8080, debug=True)
