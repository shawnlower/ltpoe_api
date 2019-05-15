from datetime import timedelta
from flask import Flask, current_app, make_response, request, current_app
from flask_rebar import errors, Rebar
from functools import update_wrapper
from marshmallow import fields, Schema
from urllib.parse import unquote

# Type models
from models import TypeSchema, GetTypeQueryStringSchema, GetTypesQueryStringSchema, GetTypeResponseSchema, GetTypesResponseSchema, CreateItemResponseSchema, CreateTypeSchema, CreateItemSchema
from models import GetItemsResponseSchema, GetItemsQueryStringSchema

# Item models
from models import ItemSchema, GetItemQueryStringSchema, GetItemResponseSchema

# Property models
from models import PropertySchema, PropertyValueSchema, GetPropertiesQueryStringSchema, GetPropertiesResponseSchema

from db import SparqlDatasource as DB
from db import LtpType, LtpItem
import db

conn = DB()

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
        raise errors.NotFound()

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
    t = LtpType(**body)
    conn.create_type(t)
    # Generate URI from prefix
    return t, 201

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

    i = LtpItem(**body)
    item = conn.create_item(i.name, i.itemType)
    # Generate URI from prefix
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
    #args = rebar.validated_args

    item = conn.get_item(id)

    if not item:
        raise errors.NotFound()

    properties = conn.get_item_properties(item)

    return { 'metadata': item,
             'properties': properties,
             'num_properties': len(properties) }

    # Errors are converted to appropriate HTTP errors
    # raise errors.Forbidden()


app = Flask(__name__)
app.config['PREFIX'] = 'schema:'
app.config['BASE'] = 'ltp:'
rebar.init_app(app)

if __name__ == '__main__':
    app.run()

@app.after_request
def apply_caching(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

