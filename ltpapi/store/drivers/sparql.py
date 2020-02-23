import logging

import functools
import time

from rdflib import ConjunctiveGraph, Graph, RDF, RDFS, OWL, XSD
from rdflib.namespace import NamespaceManager, Namespace

from ltpapi.store.store import Datastore
from ltpapi.models import LtpItem, LtpType, LtpProperty

# Setup a logger for use outside the flask context
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
log = logging.getLogger()

def log_time(func):
    @functools.wraps(func)
    def wrapper_timed(*args, **kwargs):
        start_t = time.perf_counter()
        rv = func(*args, **kwargs)
        elapsed_t = time.perf_counter() - start_t
        log.warn("{} ({}, {}) executed in {}".format(func.__name__, args, kwargs, elapsed_t))
        return rv
    return wrapper_timed


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

    @log_time
    def _get_types(self, root=OWL.Thing):
        # rv = super()._get_types(root)
        # return rv
        sparql = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>

        SELECT ?s ?rdf_type ?rdfs_label ?rdfs_comment
        WHERE {
          ?s rdfs:subClassOf* owl:Thing .
          ?s rdfs:label ?rdfs_label .
          ?s rdfs:comment ?rdfs_comment .
          ?s rdf:type ?rdf_type .
        }
        """
        resp = self._graph.query(sparql)
        types = []
        for t in resp:
            types.append(LtpType(
                    type_id=t[0],
                    name=t[2],
                    description=t[3],
                    namespace=self.namespace,
                    ))
        return types

    @log_time
    def _get_type(self, *args, **kwargs):
        rv = super()._get_type(*args, **kwargs)
        return rv
