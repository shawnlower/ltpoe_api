import logging
import os
import time
import uuid

from rdflib import ConjunctiveGraph, Graph, RDF, RDFS, OWL
from rdflib import Variable, URIRef, Literal
from rdflib.namespace import NamespaceManager, Namespace

from ltpapi.models import LtpItem, LtpType, LtpProperty
from ..utils import normalize_iri, normalize_type_id, normalize_item_id
from ltpapi.exceptions import *

# Setup a logger for use outside the flask context
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
log = logging.getLogger()

class SqliteDatastore():

    def __init__(self, config):
        self.config = config

        # Whether to create a new file for the backing store
        if not 'create' in self.config:
            self.config['create'] = "true"

        do_create = self.config.get('create').lower() == 'true'

        self._graph = ConjunctiveGraph('SQLite',
                     identifier=config['prefix'])

        if not 'file' in config:
            raise InvalidConfigurationError("Missing 'STORE_FILE' key in config")

        db_file = config['file']
        if do_create and not os.path.exists(db_file):
            log.info(f"Creating: {db_file}")
            self._graph.open(db_file, create=True)
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

    def dump(self, format='n3') -> str:
        """
        Dump the data from the store
        """
        return self._graph.serialize(format='n3')

    def load(self, filename):
        """
        Load data into the store
        """
        self._graph.parse(filename)
        self._graph.commit()

    def get_items(self, item_type_id: str, max_results=25, offset=0):
        """
        Return a list of items from the store

        @param max_results: The maximum number of results to return.
        @type max_results: int
        @param offset: For pagination, the start of the results
        @type offset: int
        @param item_type_id: The local ID of the type, e.g. 'Book'
        @type item_type_id: str
        """

        if item_type_id:
            item_type = URIRef(self.config['prefix'] + item_type_id)
            subjects = self._graph.subjects(RDF.type, item_type)
        else:
            all_types = self._graph.transitive_subjects(RDFS.subClassOf, OWL['Thing'])
            subjects = []
            for item_type in all_types:
                subjects += self._graph.subjects(RDF.type, item_type)

        items = []
        for entity in subjects:
            # extract the localname / ID portion of the IRI
            item_id = entity.partition(self.config['prefix'])[2]
            item = self.get_item(item_id)
            if item:
                items.append(item)

        return (items, False)


    def _create_property(self, name: str, description: str,
            domain=[], prop_range=[]) -> LtpProperty:
        """
        @param name: A name for the property
        @param description: A description of the property
        @param domain: A list of types for which the property applies
        @param prop_range: A list of types that values of the property can
                           take

        Example:

        _create_property('author', 'The author of a CreativeWork',
                         [ LTP.Book, LTP.Movie ], 
                         [ LTP.Person ])
        """
        pass

    def get_item_properties(self, item: LtpItem):
        """
        Return all properties for a given item
        """
        property_map = {}

        property_dict = dict(self._graph.predicate_objects(
            self._local_to_uriref(item.item_id)))

        # Get first of RDFS.label or LTP.name
        name_prop = next(i for i in property_dict
                if i in [RDFS.label, self.namespace.name])
        property_map['name'] = str(property_dict[name_prop])

        property_map['created'] = str(property_dict[self.namespace.created])
        property_map['datatype'] = str(property_dict[RDF.type].partition(self.namespace)[2])
        return property_map
        

    def _get_property(self, property_uri: "URIRef") -> LtpProperty:
        """
        Return a single property from the store

        @param property_uri: The URIRef of the property, e.g. 'name'
        """
        ns = self.namespace

        assert type(property_uri) == URIRef

        # Ensure property exists
        if not property_uri in self._graph.predicates():
            raise InvalidPropertyError(f'Property does not exist: {property_uri}')

        label = str(self._get_label(property_uri) or "")
        desc = str(self._get_description(property_uri) or "")
        return LtpProperty(name=label, description=desc)


    def _get_description(self, uri):
        values = list(self._graph[uri:RDFS.comment])
        if values:
            return values[0]
        else:
            return None


    def _get_label(self, uri):
        values = list(self._graph[uri:RDFS.label])
        if values:
            return values[0]
        else:
            return None


    def _uri_to_local(self, uri):
        return uri.partition(self.config['prefix'])[2]

    def get_property(self, property_id: str) -> LtpProperty:
        """
        Return a single property from the store

        @param property_id: The local ID of the property, e.g. 'name'
        """
        ns = self.namespace

        # Ensure property exists
        return self._get_property(ns[property_id])

    def _reserve_iri(self, iri, auto_suffix_max=0):
        """
        Reserve a name in the store

        On success, return the name
        On failure, return False
        """
        uriref = URIRef(iri)
        found = False
        for suffix in [''] + [str(n) for n in range(auto_suffix_max)]:
            existing = list(self._graph[uriref])
            if existing:
                continue

            # Create metadata
            # A unique ID to prevent collisions
            # A timestamp to allow async cleanup
            lock_id = URIRef(uuid.uuid4().urn)
            lock_ts = Literal(time.time_ns())
            created = self._local_to_uriref('created')
            self._graph.add((uriref, created, lock_ts))

            # Query again to ensure it's still unique
            unexpected = [e for e in self._graph[uriref:created] if not e == lock_ts]
            if unexpected: # collision
                continue
            else:
                found = True
                break

        return uriref if found else False


    def create_type(self, name: str, description: str,
            parent_name=None) -> LtpType:
        """
        @param name: A name for the type
        @param description: A description of the type
        @param parent_name: Parent type name

        Example:

        _create_type('Book', 'A physical or digital book')
        """
        ns = self.namespace

        if parent_name:
            # Lookup up parent type
            parent = self._get_type(ns.term(parent_name)).get_uri()
        else:
            parent = OWL.Thing

        name = normalize_type_id(name)

        uri = None
        for suffix in [''] + [str(n) for n in range(99)]:
            term = ns.term(name + suffix)
            if not term in self._graph.subjects():
                uri = term
                break

        if not uri:
            raise InvalidTypeError(f"All permutations of {name} taken.")

        # Add the statements for a new type
        statements = [
            (uri, RDF.type, OWL.Class),
            (uri, RDFS.subClassOf, parent),
            (uri, RDFS.comment, Literal(description)),
            (uri, RDFS.label, Literal(name)),
            (uri, ns.name, Literal(name)) ]

        for statement in statements:
            self._graph.add(statement)

        return self._get_type(uri)

    def _get_type(self, type_uri) -> LtpType:

        triple = (type_uri, RDF.type, OWL.Class)
        if not triple in self._graph:
            raise NotFoundError(f"Type not found: {type_uri}")

        name = next(self._graph[type_uri:RDFS.label])
        description = next(self._graph[type_uri:RDFS.comment])
        if not name or not description:
            raise InvalidTypeError(f'Incomplete type for {type_uri}')

        return LtpType(
                name=name,
                description=description,
                type_id=type_uri.partition(self.namespace)[2],
                namespace=self.namespace,
                )


    def get_type(self, name):
        self._get_type(self.namespace.term(name))

    def _local_to_uriref(self, localname):
        return URIRef(self._local_to_uri(localname))

    def _local_to_uri(self, localname):
        return self.config['prefix'] + localname


    def create_item(self, name: str, item_type: str, properties={}) -> LtpType:
        """
        Create a new item

        @param name: A printable label for the item
        @param item_type: The id of the type of item to create
        @param properties: A dict of additional {property_id: value} to set
        """

        ns = self.namespace

        if 'name' in properties and properties['name'] != name:
            raise Exception("Invalid request. name passed multiple times")

        # name is actually just another property
        properties['name'] = name

        # Ensure all passed properties are valid
        invalid_props = []
        for prop_id in properties:
            prop = self.get_property(prop_id)


        if invalid_props:
            raise InvalidPropertyError(
                    f"Invalid properties: {str(invalid_props)}")

        ns = self.namespace

        norm_name = normalize_item_id(name)
        item_id = self._reserve_iri(self.config['prefix'] + norm_name)

        # properties is a dict() e.g.:
        # { ns.created: <rdflib.term.Literal>, ...}
        properties = dict(self._graph[ns[item_id]])

        try:
            item = LtpItem(
                item_id=item_id,
                name=properties[RDFS.label],
                created=properties[ns.created],
                item_type=properties[RDF.type],
            )
        except KeyError as e:
            #log.warning("Invalid item in DB: item={}. Error: {}".format(
            #    item_id,
            #    str(e)
            #))
            return None

        return item

    def get_item(self, item_id: str):
        """
        Return a single item definition.
        """
        ns = self.namespace

        # properties is a dict() e.g.:
        # { ns.created: <rdflib.term.Literal>, ...}
        properties = dict(self._graph[ns[item_id]])
        try:
            item_type = properties[RDF.type].partition(self.config['prefix'])[2]
            item = LtpItem(
                item_id=item_id,
                name=properties[RDFS.label],
                created=properties[ns.created],
                item_type=item_type,
            )
        except KeyError as e:
            log.warning("Invalid item in DB: item={}. Error: {}".format(
                item_id,
                str(e)
            ))
            return None

        return item

