import click
from flask import Flask, current_app, make_response, request, current_app
from flask_rebar import Rebar

from . import utils

def create_app():
    app = Flask(__name__)
    app.config['PREFIX'] = 'schema:'
    app.config['BASE'] = 'ltp:'

    # Add all commands from the utils module
    cmds = [ v for v in utils.__dict__.values() if type(v) == click.Command]
    [ app.cli.add_command(cmd) for cmd in cmds ]

    return app

