from datetime import datetime
import logging
import os
import re
import time
import uuid

from rdflib import ConjunctiveGraph, Graph, RDF, RDFS, OWL, XSD
from rdflib.namespace import NamespaceManager, Namespace

from ltpapi.store.store import Datastore

# Setup a logger for use outside the flask context
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
log = logging.getLogger()

class SqliteDatastore(Datastore):

    def __init__(self, config):
        super().__init__(config)

        # Whether to create a new file for the backing store
        if 'create' not in self.config:
            self.config['create'] = "true"

        do_create = self.config.get('create').lower() == 'true'

        self._graph = ConjunctiveGraph('SQLite',
                                       identifier=config['prefix'])

        if 'file' not in config:
            raise InvalidConfigurationError("Missing 'STORE_FILE' key in config")

        db_file = config['file']
        if do_create and not os.path.exists(db_file) \
            or os.stat(db_file).st_size == 0:
                log.info(f"Creating: {db_file}")
                self._graph.open(db_file, create=True)
                self._graph.commit()
        else:
            log.info(f"Using existing DB: {db_file}")
            self._graph.open(db_file, create=False)

        # Bind our namespace
        self.namespace = Namespace(self.config['prefix'])
        self._namespace_manager = NamespaceManager(self._graph)
        self._namespace_manager.bind(
                'ltp',
                self.namespace,
                override=False)

        self._graph.namespace_manager = self._namespace_manager

