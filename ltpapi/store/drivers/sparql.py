import logging

import functools
import time

from rdflib import ConjunctiveGraph, Graph, RDF, RDFS, OWL, XSD
from rdflib.namespace import NamespaceManager, Namespace
from rdflib.term import Variable

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
    def _get_types(self, root=OWL.Thing, all_properties=False):
        #rv = super()._get_types(root)
        #return rv
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

        # We can optimize by issuing a single SPARQL query for all properties
        # of all types
        type_uri_list = [str(t[0]) for t in resp]
        # if all_properties:
        self._get_properties_for_types(type_uri_list, all_properties)

        # Store types in type dict of { 'http://type_uri/': LtpType }
        # The rows retrieved above should be unique, but log errors
        # in case they're not
        types = {}
        for t in resp:
            type_uri=t[0]
            # type_id is the local part
            type_id = type_uri.partition(self.config['prefix'])[2]
            name=t[2]
            description=t[3]
            if str(type_uri) in types:
                log.warn("Duplicate entry found for {}".format(type_id))

            # Enhance with properties if requested
            properties = []
            if all_properties:
                properties = self.get_properties_for_type(type_id, all_properties)

            # Append a new type
            types[str(type_uri)] = LtpType(
                    type_id=type_id,
                    name=name,
                    description=description,
                    namespace=self.namespace,
                    properties=properties
            )

        return types.values()

    @log_time
    def _get_type(self, *args, **kwargs):
        rv = super()._get_type(*args, **kwargs)
        return rv

    @log_time
    def _get_properties_for_type(self, type_id: str, all_properties=False):
        # rv = super()._get_properties_for_type(type_id, all_properties)
        # return rv
        if all_properties:
            sparql="""
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX ltp: <$PREFIX>

                SELECT ?prop ?label ?comment ?domain ?range
                WHERE {
                  <$TYPE_ID> rdfs:subClassOf* ?class .
                  ?prop rdfs:range ?range .
                  ?prop rdfs:domain ?domain .
                  ?prop rdfs:label ?label .
                  OPTIONAL { ?prop rdfs:comment ?_comment } .
                      BIND(COALESCE(?_comment, "") as ?comment)
                }
                LIMIT 25
            """
        else:
            sparql="""
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX ltp: <$PREFIX>

                SELECT ?prop ?label ?comment ?domain ?range
                WHERE {
                  ?prop rdfs:domain <$TYPE_ID> .
                  ?prop rdfs:range ?range .
                  ?prop rdfs:domain ?domain .
                  ?prop rdfs:label ?label .
                  OPTIONAL { ?prop rdfs:comment ?_comment } .
                      BIND(COALESCE(?_comment, "") as ?comment)
                }
                LIMIT 25
            """

        # Escaping {} is a pain
        replacements = {
            '$PREFIX': self.config['prefix'],
            '$TYPE_ID': type_id,
        }
        for k, v in replacements.items():
            sparql = sparql.replace(k, v)

        resp = self._graph.query(sparql)

        # We can optimize by issuing a single SPARQL query for all properties
        # of all types

        #for var in resp.vars:
        #    properties[str(var)] = {}

        properties = {}
        for binding in resp.bindings:
            # The uri of the property
            uri = str(binding[Variable('prop')])
            properties.setdefault(uri, {})
            properties[uri].setdefault('range', [])
            properties[uri].setdefault('domain', [])

            properties[uri]['label'] = binding[Variable('label')]
            properties[uri]['description'] = binding[Variable('comment')]
            prop_range = binding[Variable('range')]
            prop_domain = binding[Variable('domain')]
            if prop_range and not prop_range in properties[uri]['range']:
                properties[uri]['range'].append(prop_range)
            if prop_domain and not prop_domain in properties[uri]['domain']:
                properties[uri]['domain'].append(prop_domain)

        prop_items = []
        for prop_uri, v in properties.items():
            range_values = [
                    self._get_range(uri)
                    for uri in v['range']
                    if v['range']
            ]
            domain_values = [
                    uri.partition(self.namespace)[2]
                    for uri in v['domain']
                    if v['domain']
            ]
            prop = LtpProperty(
                v['label'],
                self.namespace,
                description=v['description'],
                property_range=range_values,
                property_domain=domain_values,
            )
            prop.property_id = prop_uri.partition(self.namespace)[2]
            prop_items.append(prop)
        return prop_items

    @log_time
    def _get_properties_for_types(self, type_list, all_properties=False):
        """
        Return a dict of {'type_uri': [LtpProperty]}
        :param type_list: type_uri[]
        :param all_properties: bool: Retrieve transitive properties
        """
        rv = [self._get_properties_for_type(t, all_properties) for t in type_list]

        return rv
