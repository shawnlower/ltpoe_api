import os
from pprint import pprint

import click
from flask import Flask, current_app, make_response, request, current_app
from flask_rebar import Rebar

from . import utils
from .store import get_connection

def create_app(rebar):
    app = Flask(__name__)
    rebar.init_app(app)
    app.config.from_pyfile('config.py')
    if 'APP_CONFIG' in os.environ:
        app.logger.info(f'Loading config from {os.environ["APP_CONFIG"]}')
        app.config.from_envvar('APP_CONFIG')

    conn = get_connection(app)
    app.logger.info(f'Created connection using {app.config["STORE_TYPE"]}')

    # Add all commands from the utils module
    cmds = [ v for v in utils.__dict__.values() if type(v) == click.Command]
    [ app.cli.add_command(cmd) for cmd in cmds ]

    return app

