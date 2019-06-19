from rdflib import ConjunctiveGraph, Graph, RDF, RDFS, OWL
from rdflib import Variable, URIRef

from ltpapi.models import LtpItem, LtpType, LtpProperty

class SqliteDatastore():
    def __init__(self, config):
        self.config = config

        # Whether to create a new file for the backing store
        do_create = self.config.get('create', 'true').lower() == 'true'

        self._graph = ConjunctiveGraph('SQLite',
                     identifier=config['prefix'])
        self._graph.open(config['file'], create=do_create)

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
            id = entity.partition(self.config['prefix'])[2]
            items.append(self.get_item(id))

        return (items, False)

    def get_item(self, id: str):
        """
        Return a single item definition.
        """
        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX schema: <http://schema.org/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ltp: <{self.config['prefix']}>

            SELECT DISTINCT ?iri ?name ?itemType ?created
            WHERE {{
                BIND(ltp:{id} as ?iri) .

               ?iri rdfs:label ?name .
               ?iri rdf:type ?itemType .
               # ?iri ltp:created ?created .
            }}
            ORDER BY ?type
        """
        response = self._graph.query(query)
        bindings = response.bindings
        if not bindings:
            return None
        if len(bindings) > 1:
            logger.warn("Received {} bindings. Expected a single item".format(
                len(bindings)))
        binding=bindings[0]

        item = LtpItem(
            id=id,
            name=binding[Variable('name')],
            itemType=binding[Variable('itemType')]
        )
        # created=binding[Variable('created')],

        return item

