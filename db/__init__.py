from datetime import datetime
import json
from rdflib import Graph
import requests
from requests.auth import HTTPBasicAuth

DEFAULT_CONFIG = {
    'endpoint': 'http://localhost:3030/test',
    'username': 'admin',
    'password': 'voiafa8s9dasdf23'
}


class LtpItem():
    '''Class for a single "Item" object'''
    name: str
    datatype: str
    id: str = ""
    description: str = ""
    properties = []
    def __init__(self, name, datatype, id, description=None):
        self.name = name
        self.id = id
        self.description = description

class LtpType():
    '''Class for a single "Type" object'''
    name: str
    iri: str = ""
    description: str = ""
    def __init__(self, name, iri, description):
        self.name = name
        self.iri = iri
        self.description = description

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
        self.datatype = datatype

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
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX schema: <http://schema.org/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>

        INSERT {{
            <{ltp_type.iri}> rdf:type rdfs:Class .
            <{ltp_type.iri}> rdfs:label "{ltp_type.name}" .
            <{ltp_type.iri}> rdfs:comment "{ltp_type.description}"
        }} WHERE {{}}
        """

        auth=HTTPBasicAuth(self.config['username'], self.config['password'])

        response = requests.post(self.config['endpoint'] + '/update', data={'update': query}, auth=auth)
        response.raise_for_status()

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
          ORDER BY ASC(?name)
          LIMIT {query_limit}
          OFFSET {query_offset}
          """
        response = requests.post(self.config['endpoint'] + '/query', data={'query': query})
        results = sparqlResultToTypes(json.loads(response.text))

        # Query is for one more than the user requested, so we know if addt'l results exist
        if len(results) == query_limit:
            more = True
            results.pop()
        else:
            more = False

        response.raise_for_status()
        return (results, more)

    def get_properties_for_type(self, typeIri, max_results=25, offset=0):
        """
        Retrieve the properties for a given type
        @param typeIri: string: the IRI of a given type
        """

        if max_results < 1 or max_results > 100:
            query_limit = 26;
        else:
            query_limit = max_results + 1

        query_offset = offset;

        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX schema: <http://schema.org/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ltp: <http://shawnlower.net/o/>

            SELECT DISTINCT ?property ?name ?description ?range WHERE {{
                BIND(<{typeIri}> as ?type)
                ?property a rdf:Property .
                OPTIONAL {{ ?property rdfs:label ?label }} BIND(COALESCE(?label, ?property) as ?name)
                OPTIONAL {{ ?property rdfs:comment ?description }} .
                ?property schema:domainIncludes ?type .
                ?property schema:rangeIncludes ?range
            }}
            ORDER BY ASC(?propertyName)
            LIMIT {query_limit}
            OFFSET {query_offset}
            """
        response = requests.post(self.config['endpoint'] + '/query', data={'query': query})
        bindings = json.loads(response.text)['results']['bindings']
        properties = []
        for binding in bindings:
            p = LtpProperty(
                name=binding['name']['value'],
                iri=binding['property']['value'],
                description=binding['description']['value'],
                datatype=binding['range']['value'])
            properties.append(p)

        # Query is for one more than the user requested, so we know if addt'l results exist
        if len(properties) == query_limit:
            more = True
            properties.pop()
        else:
            more = False

        response.raise_for_status()
        return (properties, more)

    def get_type(self, type_iri):
        """
        Return a single type definition.
        """
        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX schema: <http://schema.org/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT DISTINCT ?iri ?name ?description
            WHERE {{
                BIND({type_iri} as ?iri) .

               ?iri rdfs:label ?name .
               ?iri rdfs:comment ?description
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

            SELECT DISTINCT ?iri ?name ?description ?datatype
            WHERE {{
                BIND(ltp:{id} as ?iri) .

               ?iri rdfs:label ?name .
               ?iri rdfs:comment ?description .
               ?iri rdf:type ?datatype .
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
            datatype=binding['datatype']['value'])

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
                OPTIONAL {{ ?value rdf:type ?datatype }}
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
                   ?property schema:rangeIncludes ?datatype
              }}
              FILTER (BOUND(?subtype))
        """

        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX schema: <http://schema.org/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT DISTINCT ?subtype ?property ?name ?description ?datatype
            WHERE {{
              BIND( <{type_iri}> as ?type)
              {{
                {{ ?property rdfs:domainIncludes ?type }} UNION
                {{ ?property schema:domainIncludes ?type }}
                ?property schema:rangeIncludes ?datatype .
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
                    datatype=binding['datatype']['value'])
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
                    description=binding['description']['value'])
    return t
