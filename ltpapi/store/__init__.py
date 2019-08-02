import click
import logging

from flask import g

from .. import exceptions as err
from .drivers import SqliteDatastore, SparqlDatastore
from .utils import unprefix_config

# Setup a logger for use outside the flask context
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
log = logging.getLogger()


def get_connection(app):
    """
    Return a connection object, using the configuration details in the app
    """
    if 'conn' in g:
        log.debug(f"Returning existing connection: {str(g.conn)}")
        return g.conn

    store_config = unprefix_config(app.config, 'STORE_')

    if not store_config:
        raise(err.InvalidConfigurationError(f'Missing store_config in app configuration'))

    store_type = store_config.get('type').lower()

    if store_type == 'sparqldatastore':
        conn = SparqlDatastore(store_config)
    elif store_type == 'sqlite':
        conn = SqliteDatastore(store_config)
    else:
        raise(err.InvalidConfigurationError(f'Invalid store type: "{store_type}"'))

    g.conn = conn
    return conn


def init_db(app):
    log.info("Initializing DB")

    return # test
    from . import commands  # prevent circular reference

    cmds = [v for v in commands.__dict__.values() if type(v) == click.Command]
    [app.cli.add_command(cmd) for cmd in cmds]
