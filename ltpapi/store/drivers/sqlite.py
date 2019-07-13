from rdflib import ConjunctiveGraph, Graph, RDF, RDFS, OWL
from rdflib import Variable, URIRef, Literal
from rdflib.namespace import NamespaceManager, Namespace

from ltpapi.models import LtpItem, LtpType, LtpProperty
from ..utils import normalize_iri, normalize_type_id, normalize_item_id
from ltpapi.exceptions import *


class SqliteDatastore():
    def __init__(self, config):
        self.config = config

        # Whether to create a new file for the backing store
        do_create = self.config.get('create', 'true').lower() == 'true'

        self._graph = ConjunctiveGraph('SQLite',
                     identifier=config['prefix'])
        self._graph.open(config['file'], create=do_create)

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

    def get_items(self, itemTypeId: str, max_results=25, offset=0):
        """
        Return a list of items from the store

        @param max_results: The maximum number of results to return.
        @type max_results: int
        @param offset: For pagination, the start of the results
        @type offset: int
        @param itemTypeId: The local ID of the type, e.g. 'Book'
        @type itemTypeId: str
        """

        if itemTypeId:
            item_type = URIRef(self.config['prefix'] + itemTypeId)
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

    def _get_property(self, property_uri: "URIRef") -> LtpProperty:
        """
        Return a single property from the store

        @param property_uri: The URIRef of the property, e.g. 'name'
        """
        ns = self.namespace

        assert type(property_uri) == URIRef

        # Ensure property exists
        t = (prop_uri, RDF.type, OWL.DatatypeProperty)
        if not t in self._graph:
            raise InvalidPropertyError(f'Property does not exist: {property_id}')
        raise NotImplementedError

    def get_property(self, property_id: str) -> LtpProperty:
        """
        Return a single property from the store

        @param property_id: The local ID of the property, e.g. 'name'
        """
        ns = self.namespace

        # Ensure property exists
        prop_uri = self._get_property(ns[property_id])

        raise NotImplementedError('get_property not implemented')

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

        raise
        ns = self.namespace

        # properties is a dict() e.g.:
        # { ns.created: <rdflib.term.Literal>, ...}
        properties = dict(self._graph[ns[item_id]])

        try:
            item = LtpItem(
                id=item_id,
                name=properties[RDFS.label],
                created=properties[ns.created],
                itemType=properties[RDF.type],
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
            item = LtpItem(
                item_id=item_id,
                name=properties[RDFS.label],
                created=properties[ns.created],
                itemType=properties[RDF.type],
            )
        except KeyError as e:
            #log.warning("Invalid item in DB: item={}. Error: {}".format(
            #    item_id,
            #    str(e)
            #))
            return None

        return item

