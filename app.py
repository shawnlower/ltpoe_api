from datetime import timedelta
from flask import Flask, current_app, make_response, request, current_app
from flask_rebar import errors, Rebar
from functools import update_wrapper
from marshmallow import fields, Schema

from models import TypeSchema, GetTypeQueryStringSchema, GetTypesQueryStringSchema, GetTypeResponseSchema, GetTypesResponseSchema, CreateTypeSchema

from db import SparqlDatasource as DB
from db import LtpType
import db

conn = DB()

rebar = Rebar()

# All handler URL rules will be prefixed by '/v1'
registry = rebar.create_handler_registry(prefix='/v1')

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
    

    iri = current_app.config['PREFIX'] + name

    t = conn.get_type(iri)

    if not t:
        raise errors.NotFound()

    properties = conn.get_properties(t.iri, args.get('all_properties', False))

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
    t.iri = conn.generate_item_name(t.name, t.description)
    conn.create_type(t)
    # Generate URI from prefix
    return t, 201

#create_app().run()
app = Flask(__name__)
app.config['PREFIX'] = 'schema:'
rebar.init_app(app)

if __name__ == '__main__':
    app.run()

@app.after_request
def apply_caching(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Access-Control-Allow-Origin"] = "*"
    #import pdb; pdb.set_trace()
    return response

