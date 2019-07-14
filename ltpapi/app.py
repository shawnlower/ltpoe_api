import os

import click
from flask import Flask, current_app, g

from . import utils
from .store import init_db

def create_app(rebar):
    app = Flask(__name__)
    rebar.init_app(app)
    app.config.from_pyfile('config.py')
    if 'APP_CONFIG' in os.environ:
        app.logger.info(f'Loading config from {os.environ["APP_CONFIG"]}')
        app.config.from_envvar('APP_CONFIG')

    init_db(app)

    app.logger.info(f'Created connection using {app.config["STORE_TYPE"]}')

    return app

