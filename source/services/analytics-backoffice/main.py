"""
This module contains main endpoints of analytics backoffice API.
"""
import contextlib
from decimal import Decimal

import boto3
from flask import Flask, jsonify, request, wrappers
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


class FlaskApp(Flask):
    """
    This class redefines Flask class.
    """

    def __init__(self, name):
        Flask.__init__(self, name)
        CORS(self)
        self.json_provider_class = FlaskAppEncoder
        self.json = FlaskAppEncoder(self)

        self.config["athena"] = boto3.client("athena")
        self.config["database"] = boto3.resource("dynamodb",)

        @self.after_request
        def after_request(response: wrappers.Response):
            """after_request"""
            if response.status_code == 308:
                adapter = app.url_map.bind(request.host)
                # pylint: disable=unpacking-non-sequence
                endpoint, _ = adapter.match(path_info=f"{request.path}/", method=request.method)
                endpoint_function = app.view_functions[endpoint]
                return endpoint_function()
            return response

        @self.get("/")
        def default():
            """
            Default endpoint.
            """
            return jsonify(), 204


app = FlaskApp(__name__)
app.register_blueprint(applications_endpoints, url_prefix="/applications")
app.register_blueprint(remote_configs_endpoints, url_prefix="/remote-configs")


if __name__ == "__main__":
    # Used when running locally.
    app.run(host="localhost", port=8080, debug=True)
