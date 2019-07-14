from datetime import timedelta
from functools import update_wrapper
from urllib.parse import unquote

from flask import Flask, current_app, make_response, request, current_app, g
from flask_rebar import Rebar
from marshmallow import fields, Schema

# e.g. PropertySchema, TypeSchema, *RequestSchema, etc
from .schema import *

# Item models
from .models import LtpType, LtpItem, LtpProperty
from . import exceptions as err

# Factory
from .app import create_app as _create_app

# Connectors, e.g. SPARQL-over-HTTP, and SQLite
from . import store
from .store import get_connection

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
    prefix = current_app.config['PREFIX']
    conn = get_connection(current_app)

    args = rebar.validated_args
    max_results = args.get('max_results', 25)
    offset = args.get('offset', 0)

    parent =  args.get('parent', None)
    if parent:
        parent_iri = prefix + parent
    else:
        parent_iri = None

    (types, more) = conn.get_types(max_results, offset, parent_iri)
    current_app.logger.debug(types)
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
    max_results = args.get('max_results', 25)
    offset = args.get('offset', 0)
    itemTypeId = args.get('itemTypeId')

    (items, more) = conn.get_items(itemTypeId)
    current_app.logger.debug(items)
    return { 'data': items, 'more': more, 'results': len(items) }

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
    max_results = args.get('max_results', 25)
    offset = args.get('offset', 0)
    all_properties = args.get('all_properties')

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

    current_app.logger.debug(f'Getting type for name: {name}')
    t = conn.get_type(name)

    if not t:
        raise err.NotFound()

    properties = conn.get_properties_for_type(t.id, args.get('all_properties', True))

    return { 'metadata': t,
             'properties': properties,
             'num_properties': len(properties) }

    # Errors are converted to appropriate HTTP errors
    # raise errors.Forbidden()

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
        name: t.name,
        description: t.description,
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
       201: CreateItemResponseSchema()
   }
)
def create_item():
    body = rebar.validated_body
    conn = get_connection(current_app)

    try:
        item = conn.create_item(body['name'], body['itemType'])
    except Exception as e:
        raise err.InternalError()

    return {'item': item}, 201

@registry.handles(
        rule='/items/<id>',
        method='GET',
        marshal_schema=GetItemResponseSchema(),
)
def get_item(id):
    """
    Get a single Item from the DB
    """

    item = conn.get_item(id)

    if not item:
        raise err.NotFound()

    properties = conn.get_item_properties(item)

    return { 'metadata': item,
             'properties': properties,
             'num_properties': len(properties) }

    # Errors are converted to appropriate HTTP errors
    # raise errors.Forbidden()

if __name__ == '__main__':
    print('Running...')
    app = create_app()
    app.run()

def create_app(rebar=rebar):

    app = _create_app(rebar)

    @app.after_request
    def apply_caching(response):
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    @app.teardown_appcontext
    def close_db(error):
        if hasattr(g, 'conn'):
            current_app.logger.debug(f'Closing connection: {g.conn}')

    return app

