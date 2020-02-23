import logging
from typing import List

from rdflib import ConjunctiveGraph, Graph, RDF, RDFS, OWL, XSD
from rdflib import Variable, URIRef, Literal
from rdflib.namespace import NamespaceManager, Namespace

from ltpapi.models import LtpItem, LtpType, LtpProperty
from ltpapi.store.utils import normalize_iri, normalize_type_id, normalize_item_id
from ltpapi.exceptions import *

# Setup a logger for use outside the flask context
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
log = logging.getLogger()

class Datastore:

    def __init__(self, config):
        self.config = config

        # Whether to create a new file for the backing store
        if 'create' not in self.config:
            self.config['create'] = "true"

        do_create = self.config.get('create').lower() == 'true'


    def close(self):
        self._graph.close()

    def dump(self, format='n3') -> str:
        """
        Dump the data from the store
        """
        return self._graph.serialize(format='n3').decode('utf-8')

    def load(self, filename):
        """
        Load data into the store
        """
        self._graph.parse(filename, format='ttl')
        self._graph.commit()

    def get_items(self, item_type_id: str = None, max_results=500, offset=0,
                  filter_props={}, query=None):
        """
        Return a list of items from the store

        @param max_results: The maximum number of results to return.
        @type max_results: int
        @param offset: For pagination, the start of the results
        @type offset: int
        @param item_type_id: The local ID of the type, e.g. 'Book'
        @type item_type_id: str
        @param filter_props: A dictionary containing properties to filter on
        @type filter_props: dict
        """

        print("item_type_id", item_type_id)
        if item_type_id:
            item_type = self.namespace.term(item_type_id)
        else:
            item_type = OWL.Thing

        item_types = self._get_types(item_type)
        subjects = []
        for item_type in item_types:
            subjects += self._graph.subjects(RDF.type, item_type)

        items = []
        for entity in subjects:
            # extract the localname / ID portion of the IRI
            item_id = entity.partition(self.config['prefix'])[2]
            item = self.get_item(item_id)
            if item:
                _filter_props = dict(filter_props)
                if 'name' in _filter_props:
                    if str(item.name) != _filter_props.pop('name'):
                        continue

                if 'item_type' in _filter_props:
                    if item.item_type != _filter_props.pop('item_type'):
                        continue

                for prop in _filter_props:
                    if prop == 'name':
                        continue
                    else:
                        log.warning((f"TODO: Not filtering for "
                                     f"{prop}={_filter_props[prop]}"))
                item.properties = self.get_item_properties(item)

                # Basic query/filtering
                if query and query.lower() not in str(item.name).lower():
                    pass
                else:
                    items.append(item)

        return items, False

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

        item_uri = self._local_to_uriref(item.item_id)

        property_dict = dict(self._graph.predicate_objects(
            item_uri))

        ###
        # get the property object
        property_list = []
        for prop_uri in property_dict:
            try:
                prop = self._get_property(prop_uri)
                propValue = list(self._graph[item_uri:prop_uri])
                print("Got property", item.item_id, prop.name, propValue)
                if len(propValue) == 0:
                    propValue = None
                elif len(propValue) > 1:
                    print("WARNING: Property length of {} for {}".format(
                        len(propValue), str(propValue)))
                prop.value = propValue[0]
                property_list.append(prop)
            except Exception as e:
                print("Couldn't lookup", prop_uri)
                print(e)

        return property_list
        ###

        # Get first of RDFS.label or LTP.name
        # name_prop = next(i for i in property_dict
        #                  if i in [RDFS.label, self.namespace.name])
        # property_map['name'] = str(property_dict[name_prop])

        # property_map['created'] = str(property_dict[self.namespace.created])
        # return property_map

    def get_namespace(self):
        """
        Return the current namespace
        """
        return self.namespace

    def _get_property(self, property_uri: "URIRef") -> LtpProperty:
        """
        Return a single property from the store

        @param property_uri: The URIRef of the property, e.g. 'name'
        """
        ns = self.namespace

        assert type(property_uri) == URIRef

        # Ensure property exists
        if not next((i for i in self._graph[property_uri:RDF.type:]
            if  i in [OWL.DatatypeProperty, OWL.ObjectProperty]), None):
            raise InvalidPropertyError(f'Property does not exist: {property_uri}')

        label = str(self._get_label(property_uri) or "")
        desc = str(self._get_description(property_uri) or "")

        # Get range and domain
        prop_range = []
        for range_item in self._graph.objects(property_uri, RDFS.range):
            range_id = range_item.partition(self.namespace)[2]
            if range_id:
                prop_range.append(range_id)
            elif range_item == XSD.string:
                prop_range.append('string')
            elif range_item == XSD.date:
                prop_range.append('date')
            elif range_item == XSD.integer:
                prop_range.append('number')
            elif range_item == XSD.dateTime:
                prop_range.append('datetime')
            else:
                log.warning(f"Ignoring out-of-namespace range item {range_item}")

        prop_domain = []
        for domain_item in self._graph.objects(property_uri, RDFS.domain):
            domain_id = domain_item.partition(self.namespace)[2]
            if domain_id:
                prop_domain.append(domain_id)
            else:
                log.warning(f"Ignoring out-of-namespace domain item {domain_item}")

        prop = LtpProperty(label, self.namespace, description=desc,
            property_range=prop_range, property_domain=prop_domain)
        prop.property_id = property_uri.partition(self.namespace)[2]

        return prop

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

    def _add_property_to_item(self, item, prop) -> LtpItem:
        print("Adding property:::::", item, prop, prop.value)
        item_uri = item.get_uri()
        prop_uri = prop.get_uri()
        value = str(prop.value)

        if not item_uri and prop_uri and value:
            raise err.InvalidPropertyError()

        # We should perform some validation on the value here
        if type(value) == URIRef or re.match('^https?://', value):
            _value = URIRef(value)
        else:
            _value = Literal(value)

        self._graph.add((item_uri, prop_uri, _value))
        self._graph.commit()

    def add_property_to_item(self, item, prop) -> LtpItem:
        return self._add_property_to_item(item, prop)

    def _delete_property_from_item(self, item, prop, value=None) -> LtpItem:
        print("Deleting property:::::", item, prop, prop.value)
        item_uri = item.get_uri()
        prop_uri = prop.get_uri()

        value = None
        if prop.value:
            value = prop.value

        if not item_uri and prop_uri and value:
            raise err.InvalidPropertyError()

        # We should perform some validation on the value here
        if type(value) == type(None):
            _value = None
        elif type(value) == URIRef or re.match('^https?://', value):
            _value = URIRef(value)
        else:
            _value = Literal(value)

        self._graph.remove((item_uri, prop_uri, _value))
        self._graph.commit()

    def delete_property_from_item(self, item, prop) -> LtpItem:
        return self._delete_property_from_item(item, prop)

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
            lock_ts = Literal(
                    datetime.utcnow().isoformat(' '),
                    datatype=XSD.dateTime)
            created = self._local_to_uriref('created')
            self._graph.add((uriref, created, lock_ts))

            # Query again to ensure it's still unique
            unexpected = [e for e in self._graph[uriref:created] if not e == lock_ts]
            if unexpected: # collision
                continue
            else:
                found = True
                break

        self._graph.commit()
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

        self._graph.commit()
        t = self._get_type(uri)
        return t

    def _get_type(self, type_uri) -> LtpType:
        """
        Returns an LtpType object.
        """

        owl_t = (type_uri, RDF.type, OWL.Class)
        rdfs_t = (type_uri, RDF.type, RDFS.Class)
        if not owl_t in self._graph or rdfs_t in self._graph:
            raise NotFoundError(f"Type not found: {type_uri}")

        name = next(self._graph[type_uri:RDFS.label], None)
        if not name:
            #raise InvalidTypeError(f'Incomplete type for {type_uri}')
            pass

        description = next(self._graph[type_uri:RDFS.comment], "<no description>")

        return LtpType(
                name=name,
                description=description,
                type_id=type_uri.partition(self.namespace)[2],
                namespace=self.namespace,
                )

    def get_properties(self, max_results=0, offset=0):
        """
        TODO: is this even necessary? Just use get_properties_for_type?
        """
        log.warning("Ignoring max_results and offset (pagination unimplemented)")
        # Return all properties that we find w/ valid IDs
        properties = filter(lambda i: i.property_id,
            map(self._get_property, self._get_properties()))
        return [list(properties), False]

    def _get_properties(self) -> List[URIRef]:
        """
        Return a list of property URIs
        """
        properties = list(self._graph[:RDF.type:OWL.DatatypeProperty]) + \
                     list(self._graph[:RDF.type:OWL.ObjectProperty])

        return properties

    def get_properties_for_type(self, type_id, recursive=True):
        return self._get_properties_for_type(self.namespace.term(type_id))

    def _get_properties_for_type(self, type_uri) -> List[URIRef]:
        """
        Return a list of URIs which are valid for a given type
        """
        properties = {}
        # Get a list of all parent types
        trans_uris = list(self._graph.transitive_objects(type_uri, RDFS.subClassOf))
        for uri in trans_uris:
            domain_uris = list(self._graph[:RDFS.domain:uri])
            for domain_uri in domain_uris:
                prop = self._get_property(domain_uri)
                if prop.property_id in properties:
                    p = properties[prop.property_id]
                    log.warn("Duplicate property key detected for {} ".format(
                            prop.property_id))
                properties[prop.property_id] = prop

        return properties.values()

    def get_type(self, name):
        return self._get_type(self.namespace.term(name))

    def get_types(self, root):
        if root:
            type_uris = list(self._get_types(self.namespace.term(root)))
        else:
            type_uris = list(self._get_types())

        types = []
        for type_uri in type_uris:
            try:
                types.append(self._get_type(type_uri))
            except NotFoundError:
                pass

        return (types, False)

    def _get_types(self, root=OWL.Thing):
        t = self._graph.transitive_subjects(RDFS.subClassOf, root)
        return t

    def _local_to_uriref(self, localname):
        return URIRef(self._local_to_uri(localname))

    def _local_to_uri(self, localname):
        return self.config['prefix'] + localname

    def _delete_item(self, item_id):
        """
        Delete an item, removing the URI and any properties.

        @param item_id: The ID of the item to delete
        """
        ns = self.namespace

        uri = self.namespace[item_id]
        print(f"Deleting: {uri}")
        self._graph.remove((uri, None, None))
        self._graph.commit()

    def delete_item(self, item_id: str):
        """
        Delete an item, removing the URI and any properties.

        @param item_id: The ID of the item to delete
        """
        return self._delete_item(item_id)

    def create_item(self, name: str, item_type: str, properties=[]) -> LtpType:
        """
        Create a new item

        @param name: A printable label for the item
        @param item_type: The id of the type of item to create
        @param properties: A list of PropertyValue {name: .., value: .., datatype}
        """

        ns = self.namespace

        # Ensure we didn't pass name in properties
        for prop in properties:
            if prop['name'] == 'name':
                raise InvalidItemError("Invalid request. name passed multiple times")

        if not self.get_type(item_type):
            raise InvalidItemError(f"Invalid type: {item_type}")

        # Ensure all passed properties are valid
        invalid_props = [ prop for prop in properties if not
                          self.get_property(prop['name'])]

        if invalid_props:
            raise InvalidPropertyError(
                f"Invalid properties: {str(invalid_props)}")

        ns = self.namespace

        norm_name = normalize_item_id(name)
        item_uri = self._reserve_iri(self.config['prefix'] + norm_name, 10)

        if not item_uri:
            raise Exception(f"Unable to generate IRI for name: {norm_name} ({name})")

        # Add the name
        name_prop = self.get_property('name')
        name_prop.value = name
        properties += [name_prop]

        # Add the type
        type_uri = URIRef(self.get_type(item_type).get_uri())
        self._graph.add((item_uri, RDF.type, type_uri))
        self._graph.add((item_uri, RDFS.label, Literal(name, datatype=XSD.string)))

        for prop in properties:
            prop_uri = URIRef(self.get_property(prop.property_id).get_uri())
            _value = prop.value
            if not _value:
                raise InvalidPropertyError
            if type(_value) == URIRef or re.match('^https?://', _value):
                value = _value
            else:
                value = Literal(_value)
            self._graph.add((item_uri, prop_uri, value))

        item = self._get_item(item_uri)
        self._graph.commit()
        return item

    def get_item(self, item_id: str):
        """
        Return a single item definition.
        """

        return self._get_item(self.namespace[item_id])

    def _get_item(self, item_id: str):
        """
        Return a single item definition.
        """

        ns = self.namespace
        # properties is a dict() e.g.:
        # { ns.created: <rdflib.term.Literal>, ...}
        properties = dict(self._graph[item_id])
        try:
            item_type = properties[RDF.type].partition(self.config['prefix'])[2]
            item = LtpItem(
                item_id=self._uri_to_local(item_id),
                name=properties[RDFS.label],
                created=properties[ns.created],
                item_type=item_type,
                namespace=ns,
            )
        except KeyError as e:
            log.warning("Invalid item in DB: item={}. Error: {}".format(
                item_id,
                str(e)
            ))
            return None

        return item

    def retype_item(self, item: "LtpItem", new_type: "LtpType"):
        """
        Change the type of an item

        @param: item: An LtpItem to be retyped
        @param: new_type: The LtpType desired for the item

        @return: None
        """

        existing_props = [p.name for p in self.get_properties_for_type(item.item_type,
            recursive=True)]
        new_props = [p.name for p in self.get_properties_for_type(new_type.name,
            recursive=True)]


        incompatible_props = [p for p in existing_props if not p in new_props]
        if incompatible_props:
            types_string = ", ".join(incompatible_props)
            err = 'Incompatible types. Types not present on the new type: '+\
                  types_string
            return {errors: [err]}, 400

        diff2 = [p for p in new_props if not p in existing_props ]

        log.info(f"Retyping '{item.item_id}' from {item.item_type} to "+\
                f"{new_type.type_id}. {len(diff2)} additional props in new type.")

        item_uri = item.get_uri()
        new_type_uri = new_type.get_uri()
        type_triple = self._graph[item_uri:RDF.type:]
        if type_triple and new_type_uri:
            self._graph.set((item_uri, RDF.type, new_type_uri))
            self._graph.commit()
        else:
            raise Exception("Unable to retrieve type data")


