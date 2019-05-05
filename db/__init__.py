from datetime import datetime
import json
from rdflib import Graph
import requests
from requests.auth import HTTPBasicAuth

DEFAULT_CONFIG = {
    'endpoint': 'http://localhost:3030/schema',
    'username': 'admin',
    'password': 'voiafa8s9dasdf23'
}


class LtpItem():
    '''Class for a single "Item" object'''
    name: str
    dataType: str
    id: str = ""
    description: str = ""
    properties = []
    def __init__(self, name, dataType, id, description=None):
        self.name = name
        self.id = id
        self.description = description

class LtpType():
    '''Class for a single "Type" object'''
    name: str
    iri: str = ""
    description: str = ""
    created: str = ""
    properties = []
    def __init__(self, name, description, created="", iri=None):
        self.name = name
        self.description = description
        self.iri = iri
        self.created = created

class LtpProperty():
    '''Class for a single "Property" object'''
    name: str
    iri: str = ""
    value: str = ""
    datatype: str = ""
    def __init__(self, name, iri, value=None, description=None, datatype=None):
        self.name = name
        self.iri = iri
        self.value = value
        self.description = description
        self.dataType = description

class SparqlDatasource():
    def __init__(self, config = DEFAULT_CONFIG):
        self.config = config
        self.g = Graph('SPARQLStore')
        self.g.open(config['endpoint'])
        print("Initialized SPARQL backend.")

    def create_item(self, name):
        pass

    def get_items(self, max_results=25, offset=0, filters=[]):
        """
        Return a list of items

        @param max_results: The maximum number of results to return.
        @type max_results: int
        @param offset: For pagination, the start of the results
        @type offset: int
        @param filters: A list of Filter items to apply
        @type filters: [Filter]
        """
        # for item in self.g.triples


    def create_type(self, ltp_type):
        """
        create a new Type
        @param ltp_type: an LtpType object
        """

        t = ltp_type
        # Generate a unique name
        if t.iri:
            raise(Exception('Unexpected IRI'))

        timestamp = datetime.now().strftime('%s')
        name = t.name.title()
        suffix = ''
        for suffix in [''] + [str(n) for n in range(9)]:
            t.iri = f'http://shawnlower.net/o/{name}{suffix}'

            query = f"""
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX schema: <http://schema.org/>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX ltp: <http://shawnlower.net/o/>

                INSERT {{
                   <{t.iri}> rdf:type      rdfs:Class .
                   <{t.iri}> rdfs:label    "{ltp_type.name}" .
                   <{t.iri}> rdfs:comment  "{ltp_type.description}" .
                   <{t.iri}> ltp:created   "{timestamp}"
                }} WHERE {{
                   OPTIONAL {{ <{t.iri}> ?p [] }} .
                   BIND(COALESCE(?p, "missing") as ?flag)
                   FILTER(?flag = "missing")
                }}
                """

            print(f'create_type: Query: {query}')
            auth=HTTPBasicAuth(self.config['username'], self.config['password'])

            response = requests.post(self.config['endpoint'] + '/update', data={'update': query}, auth=auth)
            response.raise_for_status()

            t_check = self.get_type(t.iri)
            if t_check and t_check.created == timestamp:
                return t
        raise(Exception("Unable to create item"))

    def get_types(self, max_results=25, offset=0, parent_iri=None):
        if max_results < 1 or max_results > 100:
            query_limit = 26;
        else:
            query_limit = max_results + 1

        query_offset = offset;

        # Retrieve and bind the properties of any subclasses as well.
        # This gets inserted into the main query below.
        subclass_block= f"{parent_iri} rdfs:subClassOf* ?iri ."

        query = f"""
          PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
          PREFIX schema: <http://schema.org/>
          PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
          PREFIX owl: <http://www.w3.org/2002/07/owl#>

          SELECT DISTINCT ?iri ?name ?description WHERE {{

             { subclass_block if parent_iri else '' }

            {{ ?iri rdf:type owl:Class . }}
              UNION
            {{ ?iri rdf:type rdfs:Class . }}
            ?iri rdfs:label ?name .
            ?iri rdfs:comment ?description
          }}
          LIMIT {query_limit}
          OFFSET {query_offset}
          """
        response = requests.post(self.config['endpoint'] + '/query', data={'query': query})
        response.raise_for_status()

        results = sparqlResultToTypes(json.loads(response.text))
        if not results:
            return ([], False)

        # Query is for one more than the user requested, so we know if addt'l results exist
        if len(results) == query_limit:
            more = True
            results.pop()
        else:
            more = False

        response.raise_for_status()
        return (results, more)

    def get_type(self, type_iri):
        """
        Return a single type definition.
        """
        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX schema: <http://schema.org/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ltp: <http://shawnlower.net/o/>

            SELECT DISTINCT ?iri ?name ?description ?created
            WHERE {{
                BIND(<{type_iri}> as ?iri) .

               ?iri rdfs:label ?name .
               ?iri rdfs:comment ?description .
               ?iri ltp:created ?created .
            }}
            ORDER BY ?type
        """
        response = requests.post(self.config['endpoint'] + '/query', data={'query': query})
        result = sparqlResultToTypeDetail(json.loads(response.text))
        return result

    def get_item(self, id: str):
        """
        Return a single item definition.
        """
        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX schema: <http://schema.org/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ltp: <http://shawnlower.net/o/>

            SELECT DISTINCT ?iri ?name ?description ?dataType
            WHERE {{
                BIND(ltp:{id} as ?iri) .

               ?iri rdfs:label ?name .
               ?iri rdfs:comment ?description .
               ?iri rdf:type ?dataType .
            }}
            ORDER BY ?type
        """
        response = requests.post(self.config['endpoint'] + '/query', data={'query': query})
        bindings = json.loads(response.text)['results']['bindings']
        if not bindings:
            return None
        if len(bindings) > 1:
            logger.warn("Received {} bindings. Expected a single item".format(
                len(bindings)))
        binding=bindings[0]

        item = LtpItem(
            id=id,
            name=binding['name']['value'],
            description=binding['description']['value'],
            dataType=binding['dataType']['value'])

        return item

    def get_item_properties(self, item: LtpItem):
        """
        Return all properties for a given item
        """
        
        id = item.id
        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX schema: <http://schema.org/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ltp: <http://shawnlower.net/o/>

            SELECT DISTINCT ?iri ?property ?name ?description ?value
            WHERE {{
              BIND( ltp:{id} as ?iri)
                ?iri ?property ?value .
                OPTIONAL {{ ?property rdfs:comment ?description }}
                OPTIONAL {{ ?property rdfs:label ?prop_label }}
                OPTIONAL {{ ?value rdf:type ?dataType }}
                BIND(COALESCE(?prop_label, ?property) as ?name)
            }}
            ORDER BY ?property
        """
        response = requests.post(self.config['endpoint'] + '/query', data={'query': query})
        response.raise_for_status()

        #results = sparqlResultToProperties(json.loads(response.text)) 
        bindings = json.loads(response.text)['results']['bindings']
        properties = []
        for binding in bindings:
            p = LtpProperty(
                    name=binding['name']['value'],
                    iri=binding['property']['value'],
                    description=binding['description']['value'],
                    value=binding['value']['value'])
            properties.append(p)
        return properties
        

    def get_type_properties(self, type_iri, all_properties=True):
        """
        Return all properties for a given type
        @param all_properties: Return properties for subclasses as well
        """
        
        # Retrieve and bind the properties of any subclasses as well.
        # This gets inserted into the main query below.
        subclass_block= f""" UNION {{
                ?type rdfs:subClassOf* ?subtype .
                {{ ?property rdfs:domainIncludes ?subtype }} UNION
                {{ ?property schema:domainIncludes ?subtype }}
                   ?property schema:rangeIncludes ?dataType
              }}
              FILTER (BOUND(?subtype))
        """

        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX schema: <http://schema.org/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT DISTINCT ?subtype ?property ?name ?description ?dataType
            WHERE {{
              BIND( <{type_iri}> as ?type)
              {{
                {{ ?property rdfs:domainIncludes ?type }} UNION
                {{ ?property schema:domainIncludes ?type }}
                ?property schema:rangeIncludes ?dataType .
              }}
              { subclass_block if all_properties else '' }
              OPTIONAL {{ ?property rdfs:label ?name }}
              OPTIONAL {{ ?property rdfs:comment ?description }}
              }}
            ORDER BY ?type
        """
        response = requests.post(self.config['endpoint'] + '/query', data={'query': query})

        results = sparqlResultToProperties(json.loads(response.text)) 
        response.raise_for_status()
        return results

    def generate_item_name(self, name, description):
        """
        Generate a unique name to use for a resource
        """

        # Resources 
        name = name.title()
        if description:
            desc_block = f'ltp:{name} rdfs:comment "{description}"'
        else:
            desc_block = ''

        # Reserve the name with a triple, e.g.
        # ltp:Goal <reservation> {timestamp}
        # ltp:Goal2 <reservation> {timestamp}
        suffixes = [''] + [ str(n) for n in range(99) ]

        my_ns = 'http://shawnlower.net/o/'

        timestamp = datetime.now().strftime('%s')
        # A filter criteria ensures that the insert only
        # occurs if the subject does not already exist.
        # This will always succeed, with no response.
        # A subsequent query must be done to ensure that the
        # triples were inserted.
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX schema: <http://schema.org/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX ltp: <{my_ns}>

        INSERT {{
            ltp:{name}      rdf:type rdfs:Class .
            ltp:{name}      <http://example.com/created> "{timestamp}" .
            ltp:{name}      rdfs:label "{name}" .
            {desc_block if desc_block else ''}
        }} WHERE {{
            FILTER(NOT EXISTS {{ ltp:{name} ?p ?o }}) .
        }}
        """
        print(query)

        response = requests.post(self.config['endpoint'], data={'update': query})
        response.raise_for_status()

        query = f"""
        PREFIX ltp: <{my_ns}>

        ASK {{ ltp:{name} <http://example.com/created> "{timestamp}" }}
        """
        response = requests.post(self.config['endpoint'], data={'query': query})
        response.raise_for_status()
        assert(response.json()['boolean'])


def sparqlResultToTypes(result_dict):
    """
    Take the JSON payload and return it as a list of python LtpType objects
    """
    ltp_types = []
    for binding in result_dict['results']['bindings']:
        t = LtpType(iri=binding['iri']['value'],
                    name=binding['name']['value'],
                    description=binding['description']['value'])
        ltp_types.append(t)
    return ltp_types

def sparqlResultToProperties(result_dict):
    """
    Take the JSON payload and return it as a list of python LtpType objects
    """
    props = []
    for binding in result_dict['results']['bindings']:
        p = LtpProperty(iri=binding['property']['value'],
                    name=binding['name']['value'],
                    description=binding['description']['value'],
                    datatype=binding['dataType']['value'])
        props.append(p)
    return props

def sparqlResultToTypeDetail(result_dict):
    """
    Take the JSON payload and return it as a list of python LtpType objects
    """
    t = None
    for binding in result_dict['results']['bindings']:
        t = LtpType(iri=binding['iri']['value'],
                    name=binding['name']['value'],
                    description=binding['description']['value'],
                    created=binding['created']['value'])
    return t
