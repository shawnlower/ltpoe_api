from datetime import timedelta
from functools import update_wrapper
import os
from urllib.parse import unquote

from flask import Flask, current_app, make_response, request, current_app, g
from flask_rebar import Rebar
from marshmallow import fields, Schema

# e.g. PropertySchema, TypeSchema, *RequestSchema, etc
from .schema import *

# Item models
from .models import LtpType, LtpItem, LtpProperty
from . import exceptions as err

# Connectors, e.g. SPARQL-over-HTTP, and SQLite
from . import store
from .store import get_connection, init_db

rebar = Rebar()

# All handler URL rules will be prefixed by '/v1'
registry = rebar.create_handler_registry(prefix='/api/v1')

@registry.handles(
    rule='/types/',
    method='GET',
    query_string_schema=GetTypesQueryStringSchema(),
    marshal_schema=GetTypesResponseSchema(),
)
def get_types():
    """
    Get a list of types from the DB
    """
    conn = get_connection(current_app)

    args = rebar.validated_args
    max_results = args.get('max_results', 25)
    offset = args.get('offset', 0)
    all_properties = args.get('all_properties', False)

    parent =  args.get('parent', None)

    (base_types, more) = conn.get_types(parent)
    types = []
    if all_properties:
        for t in base_types:
            t.properties = conn.get_properties_for_type(t.type_id, args.get('all_properties'))
            types.append(t)
    else:
        types = base_types

    return { 'data': types, 'more': more, 'results': len(types) }

    # Errors are converted to appropriate HTTP errors
    # raise errors.Forbidden()

@registry.handles(
    rule='/items/',
    method='GET',
    query_string_schema=GetItemsQueryStringSchema(),
    marshal_schema=GetItemsResponseSchema(),
)
def get_items():
    """
    Get a list of types from the DB
    """
    
    conn = get_connection(current_app)
    args = rebar.validated_args
    all_properties = args.get('all_properties', True)
    max_results = args.get('max_results', 500)
    query = args.get('query')
    offset = args.get('offset', 0)
    item_type_id = args.get('item_type_id')

    # We assume that any extra keys that aren't part of the official API are
    # properties on the item that we want to filter on.
    filter_props = { k: request.args.get(k) for k in request.args.keys()
        if not k in args.keys()}

    (items, more) = conn.get_items(
            item_type_id,
            filter_props=filter_props,
            query = query,
        )
    current_app.logger.debug(
        f'get_items got {len(items)} items from store: \n' \
        + '\n - '.join([str(i) for i in  items]))
    return { 'data': items, 'more': more, 'results': len(items) }

@registry.handles(
    rule='/properties/<property_id>',
    method='GET',
    marshal_schema=GetPropertyResponseSchema(),
)
def get_property(property_id):
    """
    Get a list of types from the DB
    """
    conn = get_connection(current_app)

    prop = conn.get_property(property_id)
    return {
        'data': prop
    }


@registry.handles(
    rule='/properties/',
    method='GET',
    query_string_schema=GetPropertiesQueryStringSchema(),
    marshal_schema=GetPropertiesResponseSchema(),
)
def get_properties():
    """
    Get a list of types from the DB
    """
    args = rebar.validated_args
    conn = get_connection(current_app)
    max_results = args.get('max_results', 25)
    offset = args.get('offset', 0)

    (properties, more) = conn.get_properties(max_results, offset)
    current_app.logger.debug(properties)
    return { 'data': properties, 'more': more, 'results': len(properties) }

@registry.handles(
    rule='/types/<name>',
    method='GET',
    query_string_schema=GetTypeQueryStringSchema(),
    marshal_schema=GetTypeResponseSchema(),
)
def get_type(name):
    """
    Get a list of types from the DB
    """
    args = rebar.validated_args
    conn = get_connection(current_app)
    all_properties = args.get('all_properties')

    current_app.logger.debug(f'Getting type for name: {name}')
    t = conn.get_type(name)

    if not t:
        raise err.NotFound()

    properties = conn.get_properties_for_type(t.type_id, args.get('all_properties'))

    return { 'metadata': t,
             'properties': properties,
             'num_properties': len(properties) }

    # Errors are converted to appropriate HTTP errors
    # raise errors.Forbidden()


@registry.handles(
    rule='/mappings/<resource>',
    method='GET',
    marshal_schema = {
        200: GetMappingsResponseSchema(),
    },
)
def get_mappings(resource):
    """
    Get a list of types from the DB
    """
    conn = get_connection(current_app)
    return {
        'resource': resource,
        'results': 1,
        'mappings': [{
                'ontology': 'schema.org',
                'uri': 'http://schema.org/Person',
                'rdf_type': 'abc',
                'name': 'Person',
                'mapping_type': 'exactMatch',
            }, {
                'ontology': 'wordnet.org',
                'ontology_uri': 'abc',
                'rdf_type': 'abc',
                'name': 'abc',
                'mapping_type': 'exactMatch',
                'description': 'abc',
        }]
    }


@registry.handles(
    rule='/types',
    method='POST',
    request_body_schema=CreateTypeSchema(),
    marshal_schema={
       201: TypeSchema()
   }
)
def create_type():
    body = rebar.validated_body
    conn = get_connection(current_app)

    t = conn.create_type(**body)
    # Generate URI from prefix
    type_response = {
        'name': t.name,
        'description': t.description,
    }
    return type_response, 201

@registry.handles(
    rule='/properties',
    method='POST',
    request_body_schema=CreatePropertySchema(),
    marshal_schema={
       201: PropertySchema()
   }
)
def create_property():
    body = rebar.validated_body
    p = LtpProperty(**body)
    try:
        conn.create_property(p)
    except err.InvalidProperty as e:
        raise err.BadRequest(e.msg)
    except Exception as e:
        raise err.BadRequest(str(e))

    raise err.NotImplemented('rats')

    # Generate URI from prefix
    return p, 201

@registry.handles(
    rule='/items',
    method='POST',
    request_body_schema=CreateItemSchema(),
    marshal_schema={
       201: CreateItemResponseSchema(),
       400: CreateItemResponseSchema(),
       500: CreateItemResponseSchema(),
   }
)
def create_item():
    body = rebar.validated_body
    conn = get_connection(current_app)

    name = body['name']
    item_type = body['item_type']
    properties = body['properties']

    try:
        print('create_item with', name, item_type, properties)
        item = conn.create_item(name, item_type, properties)
    except err.InvalidItemError as e:
        return {'errors': [str(e)], 'item': {}}, 400
    except Exception as e:
        print(e)
        return {'errors': 'Server Error'}, 500

    return {'item': item}, 201

@registry.handles(
        rule='/items/<item_id>',
        method='GET',
        marshal_schema=GetItemResponseSchema(),
        query_string_schema=GetItemQueryStringSchema(),
)
def get_item(item_id):
    """
    Get a single Item from the DB
    """

    conn = get_connection(current_app)
    item = conn.get_item(item_id)

    if not item:
        raise err.NotFound()

    item.properties = conn.get_item_properties(item)

    return { 'data': item }

    # Errors are converted to appropriate HTTP errors
    # raise errors.Forbidden()

@registry.handles(
        rule='/items/<item_id>',
        method='DELETE',
        marshal_schema={
            200: DeleteItemResponseSchema(),
            400: DeleteItemResponseSchema(),
            404: DeleteItemResponseSchema(),
            500: DeleteItemResponseSchema(),
        }
)
def delete_item(item_id):
    """
    Delete a single Item from the DB
    """

    try:
        conn = get_connection(current_app)
        item = conn.get_item(item_id)

        if not item:
            raise err.NotFound()

        conn.delete_item(item_id)
    except Exception as e:
        current_app.logger.error(e)
        return { "errors": [ "Unable to delete item" ]}, 400


    return { "errors": []}, 200

    # Errors are converted to appropriate HTTP errors
    # raise errors.Forbidden()

if __name__ == '__main__':
    print('Running...')
    app = create_app()
    app.run()

def create_app(rebar=rebar, config={}):

    app = Flask(__name__)
    rebar.init_app(app)

    if config:
        app.logger.info(f'Loading config: {config}')
        app.config.update(config)
    elif 'APP_CONFIG' in os.environ:
        app.logger.info(f'Loading config from {os.environ["APP_CONFIG"]}')
        app.config.from_envvar('APP_CONFIG')
    else:
        app.config.from_pyfile('config.py')

    init_db(app)

    @app.teardown_appcontext
    def close_connection(exception):
        conn = getattr(g, 'conn', None)
        if conn is not None:
            print("Closing connection to ", conn)
            conn.close()

    app.logger.info(f'Created connection using {app.config["STORE_TYPE"]}')
    @app.after_request
    def apply_caching(response):
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    return app


