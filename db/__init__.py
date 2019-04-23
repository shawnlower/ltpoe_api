from dataclasses import dataclass
import json
import requests
from requests.auth import HTTPBasicAuth

DEFAULT_CONFIG = {
    'endpoint': 'http://localhost:3030/test',
    'username': 'admin',
    'password': 'voiafa8s9dasdf23'
}


@dataclass
class LtpType():
    '''Class for a single "Type" object'''
    name: str
    iri: str = ""
    description: str = ""

@dataclass
class LtpProperty():
    '''Class for a single "Property" object'''
    name: str
    iri: str = ""
    description: str = ""
    datatype: str = ""


class SparqlDatasource():
    def __init__(self, config = DEFAULT_CONFIG):
        self.config = config
        print("Initialized SPARQL backend.")

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

    def get_properties(self, type_iri, all_properties=True):
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
                    description=binding['description']['value'])
    return t
