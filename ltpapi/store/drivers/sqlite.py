from rdflib import ConjunctiveGraph, Graph, RDF, RDFS, OWL
from rdflib import Variable, URIRef
from rdflib.namespace import NamespaceManager, Namespace

from ltpapi.models import LtpItem, LtpType, LtpProperty
from ..utils import normalize_iri, normalize_type_id, normalize_item_id


class SqliteDatastore():
    def __init__(self, config):
        self.config = config

        # Whether to create a new file for the backing store
        do_create = self.config.get('create', 'true').lower() == 'true'

        self._graph = ConjunctiveGraph('SQLite',
                     identifier=config['prefix'])
        self._graph.open(config['file'], create=do_create)

        # Bind our namespace
        self.ns = Namespace(self.config['prefix'])
        self._namespace_manager = NamespaceManager(self._graph)
        self._namespace_manager.bind(
                'ltp',
                self.ns,
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

    def get_item(self, item_id: str):
        """
        Return a single item definition.
        """
        ns = self.ns

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

