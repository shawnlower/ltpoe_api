from rdflib import ConjunctiveGraph, Graph, RDF, RDFS, OWL, URIRef

class SqliteDatastore():
    def __init__(self, config):
        self.config = config
        self._graph = ConjunctiveGraph('SQLite',
                     identifier=config['prefix'])
        self._graph.open(config['file'], create=True)

    def dump(self, format='n3') -> str:
        """
        Dump the data from the store
        """
        return self._graph.serialize(format='n3')

    def load(self, filename):
        """
        Load data into the store
        """
        return self._graph.parse(filename)

