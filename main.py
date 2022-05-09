from datetime import timedelta
from functools import update_wrapper
import os
import traceback
from urllib.parse import unquote

from flask import Flask, current_app, make_response, request, current_app, g
from flask_rebar import Rebar
from marshmallow import fields, Schema

# Rebar decorated routes
from .routes import get_routes
from .store import get_connection, init_db

if __name__ == '__main__':
    print('Running...')
    app = create_app()
    app.run()

def create_app(config={}):

    rebar = Rebar()

    # All handler URL rules will be prefixed by '/v1'
    registry = rebar.create_handler_registry(prefix='/api/v1')

    get_routes(registry, rebar)

    app = Flask(__name__)
    rebar.init_app(app)

    if config:
        app.logger.info(f'Loading config: {config}')
        app.config.update(config)
    elif 'APP_CONFIG' in os.environ:
        app.logger.info(f'Loading config from {os.environ["APP_CONFIG"]}')
        app.config.from_envvar('APP_CONFIG')
    else:
        app.config.from_pyfile('config.py')

    init_db(app)

    @app.teardown_appcontext
    def close_connection(exception):
        conn = getattr(g, 'conn', None)
        if conn is not None:
            print("Closing connection to ", conn)
            conn.close()

    app.logger.info(f'Created connection using {app.config["STORE_TYPE"]}')
    @app.after_request
    def apply_caching(response):
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    return app

