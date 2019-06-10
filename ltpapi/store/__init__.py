from ltpapi import exceptions as err
from ..models import LtpItem, LtpType, LtpProperty
from .. import exceptions as err
from .drivers import SqliteDatastore, SparqlDatastore
from .utils import unprefix_config

def get_connection(app):
    """
    Return a connection object, using the configuration details in the app
    """
    store_config = unprefix_config(app.config, 'STORE_')

    if not store_config:
        raise(err.InvalidConfiguration(f'Missing store_config in app configuration'))

    store_type = store_config.get('type').lower()

    if store_type == 'sparqldatastore':
        return SparqlDatastore(store_config)
    elif store_type == 'sqlite':
        return SqliteDatastore(store_config)
    else:
        raise(err.InvalidConfiguration(f'Invalid store type: "{store_type}"'))


