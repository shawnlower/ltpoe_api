from datetime import datetime
import json
import string

from rdflib import ConjunctiveGraph, Graph, RDF, RDFS, OWL, URIRef
import requests
from requests.auth import HTTPBasicAuth

from ltpapi import exceptions as err
from ..models import LtpItem, LtpType, LtpProperty
from .. import exceptions as err

class SparqlDatasource():
    def __init__(self, config):
        self.config = config
        self.graph = ConjunctiveGraph('SPARQLStore',
                     identifier=config['prefix'])
        self.graph.open(config['endpoint'])

    def create_property(self, prop):
        if not prop.validate():
            raise err.InvalidProperty


    def create_item(self, name, itemTypeId):

        id = normalize_item_id(name)
        itemType = URIRef(self.config['prefix'] + itemTypeId).n3()

        timestamp = datetime.now().isoformat(sep=' ',
                timespec='milliseconds')

        suffix = ''
        for suffix in [''] + [str(n) for n in range(9)]:
            iri = normalize_iri(f'http://shawnlower.net/o/{id}{suffix}')

            query = f"""
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX schema: <http://schema.org/>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                PREFIX ltp: <{self.config['prefix']}>

                INSERT {{
                   {iri} rdf:type      {itemType} .
                   {iri} rdfs:label    "{name}" .
                   {iri} ltp:created   "{timestamp}"^^xsd:dateTime .
                }} WHERE {{
                   OPTIONAL {{ {iri} ?p [] }} .
                   BIND(COALESCE(?p, "missing") as ?flag)
                   FILTER(?flag = "missing")
                }}
                """

            print(f'create_item: Query: {query}')
            auth=HTTPBasicAuth(self.config['username'], self.config['password'])

            response = requests.post(self.config['endpoint'] + '/update', data={'update': query}, auth=auth)
            response.raise_for_status()

            i_check = self.get_item(id + suffix)
            if not i_check:
                raise(Exception("Unable to create item"))

            if i_check.created == timestamp:
                return i_check
        raise(Exception("Unable to create item"))

    def get_items(self, itemTypeId: str, max_results=25, offset=0):
        """
        Return a list of items

        @param max_results: The maximum number of results to return.
        @type max_results: int
        @param offset: For pagination, the start of the results
        @type offset: int
        @param itemTypeId: The local ID of the type, e.g. 'Book'
        @type itemTypeId: str
        """

        if itemTypeId:
            item_type = URIRef(self.config['prefix'] + itemTypeId)
            subjects = self.graph.subjects(RDF.type, item_type)
        else:
            all_types = self.graph.transitive_subjects(RDFS.subClassOf, OWL['Thing'])
            subjects = []
            for item_type in all_types:
                subjects += self.graph.subjects(RDF.type, item_type)

        items = []
        for entity in subjects:
            # extract the localname / ID portion of the IRI
            id = entity.partition(self.config['prefix'])[2]
            items.append(self.get_item(id))
            
        return (items, False)


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
        name = normalize_type_id(t.name)

        suffix = ''
        for suffix in [''] + [str(n) for n in range(9)]:
            t.iri = f'http://shawnlower.net/o/{name}{suffix}'

            query = f"""
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX schema: <http://schema.org/>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX ltp: <{self.config['prefix']}>

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
          PREFIX ltp: <{self.config['prefix']}>

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
        if response.status_code == 404:
            return ([], False)

        response.raise_for_status()

        results = self.sparqlResultToTypes(json.loads(response.text))
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

    def get_properties(self, max_results=25, offset=0):
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
            PREFIX ltp: <{self.config['prefix']}>

            SELECT DISTINCT ?property ?name ?description ?range WHERE {{
                ?property a rdf:Property .
                OPTIONAL {{ ?property rdfs:label ?label }} BIND(COALESCE(?label, ?property) as ?name)
                OPTIONAL {{ ?property rdfs:comment ?description }} .
                ?property rdfs:domain ?type .
                ?property rdfs:range ?range
            }}
            ORDER BY ASC(?propertyName)
            LIMIT {query_limit}
            OFFSET {query_offset}
            """
        response = requests.post(self.config['endpoint'] + '/query', data={'query': query})
        bindings = json.loads(response.text)['results']['bindings']
        properties = []
        for binding in bindings:
            iri=binding['iri']['value']
            id=iri.partition(self.config['prefix'])[2]
            datatype_iri=binding['range']['value']
            datatype=datatype_iri.partition(self.config['prefix'])[2]
            p = LtpProperty(
                name=binding['name']['value'],
                id=id,
                description=binding['description']['value'],
                datatype=datatype)
            properties.append(p)

        # Query is for one more than the user requested, so we know if addt'l results exist
        if len(properties) == query_limit:
            more = True
            properties.pop()
        else:
            more = False

        response.raise_for_status()
        return (properties, more)

    def get_type(self, type_id: string):
        """
        Return a single type definition.
        @param type_id: string : the localname part of an IRI
        """

        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX schema: <http://schema.org/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ltp: <{self.config['prefix']}>

            SELECT DISTINCT ?iri ?name ?description ?created
            WHERE {{
                BIND(ltp:{type_id} as ?iri) .

               ?iri rdfs:label ?name .
               ?iri rdfs:comment ?description .
               OPTIONAL {{ ?iri ltp:created ?_created }} .
               BIND(COALESCE(?_created, "") as ?created) .
            }}
            ORDER BY ?type
        """
        print('get_type w/ query: ', query)
        response = requests.post(self.config['endpoint'] + '/query', data={'query': query})
        if response.status_code == 404:
            return None
        response.raise_for_status()
        result = self.sparqlResultToTypeDetail(json.loads(response.text))
        return result

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
               ?iri ltp:created ?created .
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
            created=binding['created']['value'],
            itemType=binding['itemType']['value'])

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
            PREFIX ltp: <{self.config['prefix']}>

            SELECT DISTINCT ?iri ?property ?name ?description ?value ?datatype
            WHERE {{
              BIND( ltp:{id} as ?iri)
                ?iri ?property ?value .
                OPTIONAL {{ ?property rdfs:comment ?_description }}
                OPTIONAL {{ ?property rdfs:label ?prop_label }}
                OPTIONAL {{ ?value rdf:type ?_datatype }}
                BIND(COALESCE(?_datatype, "") as ?datatype)
                BIND(COALESCE(?_description, "") as ?description)
                BIND(COALESCE(?prop_label, ?property) as ?name)
            }}
            ORDER BY ?property
        """
        response = requests.post(self.config['endpoint'] + '/query', data={'query': query})
        response.raise_for_status()

        bindings = json.loads(response.text)['results']['bindings']
        properties = []
        for binding in bindings:
            property_iri=binding['property']['value']
            property=property_iri.partition(self.config['prefix'])[2]

            datatype_iri=binding['datatype']['value']
            datatype=datatype_iri.partition(self.config['prefix'])[2]
            p = LtpProperty(
                    name=binding['name']['value'],
                    id=property,
                    datatype=datatype,
                    description=binding['description']['value'],
                    value=binding['value']['value'])
            properties.append(p)
        return properties
        

    def get_properties_for_type(self, id, all_properties=True):
        """
        Return all properties for a given type
        @param all_properties: Return properties for subclasses as well
        """
        
        # Retrieve and bind the properties of any subclasses as well.
        # This gets inserted into the main query below.
        subclass_block= f""" UNION {{
                ?type rdfs:subClassOf* ?subtype .
                {{ ?property rdfs:domain ?subtype }} UNION
                {{ ?property schema:domainIncludes ?subtype }}
                   ?property schema:rangeIncludes ?datatype
              }}
              FILTER (BOUND(?subtype))
        """


        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX schema: <http://schema.org/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ltp: <{self.config['prefix']}>

            SELECT DISTINCT ?subtype ?property ?name ?description ?datatype
            WHERE {{
              BIND( ltp:{id} as ?type)
              {{
                ?property rdfs:domain ?type .
                ?property rdfs:range ?datatype .
              }}
              UNION
              {{
                ?type rdfs:subClassOf* ?subtype .
                ?property rdfs:domain ?subtype .
                ?property rdfs:range ?datatype .
              }}
              FILTER (BOUND(?subtype))

              OPTIONAL {{ ?property rdfs:label ?name }}
              OPTIONAL {{ ?property rdfs:comment ?_description }}
              BIND(COALESCE(?_description, "no description") as ?description)
              }}
            ORDER BY ?type
        """
        print('get_properties_for_type: ', query)
        response = requests.post(self.config['endpoint'] + '/query', data={'query': query})

        results = self.sparqlResultToProperties(json.loads(response.text)) 
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

        timestamp = datetime.now().isoformat(sep=' ',
                timespec='milliseconds')
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
        PREFIX ltp: <{self.config['prefix']}>

        INSERT {{
            ltp:{name}      rdf:type rdfs:Class .
            ltp:{name}      <http://example.com/created> "{timestamp}"^^xsd:dateTime .
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
        PREFIX ltp: <{self.config['prefix']}>

        ASK {{ ltp:{name} <http://example.com/created> "{timestamp}" }}
        """
        response = requests.post(self.config['endpoint'], data={'query': query})
        response.raise_for_status()
        assert(response.json()['boolean'])


    def sparqlResultToTypes(self, result_dict):
        """
        Take the JSON payload and return it as a list of python LtpType objects
        """
        ltp_types = []
        for binding in result_dict['results']['bindings']:
            iri=binding['iri']['value']
            id=iri.partition(self.config['prefix'])[2]
            t = LtpType(id=id,
                        name=binding['name']['value'],
                        description=binding['description']['value'])
            ltp_types.append(t)
        return ltp_types

    def sparqlResultToTypeDetail(self, result_dict):
        """
        Take the JSON payload and return it as a list of python LtpType objects
        """
        t = None
        for binding in result_dict['results']['bindings']:
            iri=binding['iri']['value']
            id=iri.partition(self.config['prefix'])[2]
            t = LtpType(id=id,
                        name=binding['name']['value'],
                        description=binding['description']['value'],
                        created=binding['created'].get('value'))
        return t

    def sparqlResultToProperties(self, result_dict):
        """
        Take the JSON payload and return it as a list of python LtpType objects
        """
        props = []
        prefix = self.config['prefix']
        for binding in result_dict['results']['bindings']:
            iri=binding['property']['value']
            id=iri.partition(self.config['prefix'])[2]

            datatype_iri=binding['datatype']['value']
            if datatype_iri.startswith(prefix):
                datatype=datatype_iri.partition(prefix)[2]
            else:
                datatype=datatype_iri

            p = LtpProperty(id=id,
                        name=binding['name']['value'],
                        description=binding['description']['value'],
                        datatype=datatype)
            props.append(p)
        return props

def normalize_iri(iri: str):
    if iri.startswith('http:') or iri.startswith('https:'):
        return f'<{iri}>'
    else:
        return iri

def normalize_type_id(name: str):
    name = name.title().replace(' ', '-')
    name = ''.join([c for c in name if c in ['.'] + list(string.ascii_letters)])
    name=name.lstrip('.').rstrip('.')
    return name

def normalize_item_id(name: str):
    name = name.lower().replace(' ', '-')
    name = ''.join([c for c in name if c in ['.', '-'] + list(string.ascii_letters)])
    name=name.lstrip('.').rstrip('.')
    return name

def unprefix_config(config, prefix):
   """
   Convert PREFIX_KEY=VAL to key=val
   e.g.:
      [('STORE_ENDPOINT', 'http://localhost:3030/ltp'), ('STORE_TYPE', 'SparqlDatastore')]
         becomes
      {'endpoint': 'http://localhost:3030/ltp', 'type': 'SparqlDatastore'}
   """
   prefix = prefix.rstrip('_')
   return dict((k.split('_')[1].lower(), v) for (k,v) in config.items() if \
           k.startswith(f'{prefix}_'))

def get_connection(app):
    """
    Return a connection object, using the configuration details in the app
    """
    store_config = unprefix_config(app.config, 'STORE_')

    if not store_config:
        raise(err.InvalidConfiguration(f'Missing store_config in app configuration'))

    store_type = store_config.get('type')

    if store_type == 'SparqlDatastore':
        return SparqlDatasource(store_config)
    elif store_type == 'sqlite':
        raise(NotImplementedError(f'Store type "{store_type}" not implemented.'))
    else:
        raise(err.InvalidConfiguration(f'Invalid store type: "{store_type}"'))

