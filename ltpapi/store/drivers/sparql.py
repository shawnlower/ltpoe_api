import logging

from rdflib import ConjunctiveGraph, Graph, RDF, RDFS, OWL, XSD
from rdflib.namespace import NamespaceManager, Namespace

from ltpapi.store.store import Datastore

# Setup a logger for use outside the flask context
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
log = logging.getLogger()

class SparqlDatastore(Datastore):
    def __init__(self, config):
        super().__init__(config)

        if 'url' not in config:
            raise InvalidConfigurationError("Missing 'STORE_URL' key in config")

        self._graph = ConjunctiveGraph('SPARQLStore',
                     identifier=config['prefix'])
        self._graph.open(config['url'])

        # Bind our namespace
        self.namespace = Namespace(self.config['prefix'])
        self._namespace_manager = NamespaceManager(self._graph)
        self._namespace_manager.bind(
                'ltp',
                self.namespace,
                override=False)

        self._graph.namespace_manager = self._namespace_manager

