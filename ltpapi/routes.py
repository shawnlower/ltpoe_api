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


def get_routes(registry, rebar):
    @registry.handles(
        rule='/config',
        method='GET',
        marshal_schema=GetConfigResponseSchema(),
    )
    def get_config():
        """
        Get a list of types from the DB
        """
        conn = get_connection(current_app)
        ns = conn.get_namespace()
        return { 'namespace': ns }, 200

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

        (types, more) = conn.get_types(parent, all_properties=all_properties)
        # types = []
        #if all_properties:
        #    for t in base_types:
        #        t.properties = conn.get_properties_for_type(t.type_id, args.get('all_properties'))
        #        types.append(t)
        #else:
        #    types = base_types

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
            return { "errors": [ "Unable to delete item" ]}, 500


        return { "errors": []}, 200

    @registry.handles(
            rule='/retype/<item_id>',
            method='PUT',
            query_string_schema=RetypeItemQueryStringSchema(),
            marshal_schema={
                200: PatchItemResponseSchema(),
                400: PatchItemResponseSchema(),
                404: PatchItemResponseSchema(),
                500: PatchItemResponseSchema(),
            }
    )
    def retype_item(item_id):
        """
        Change the type of an item, e.g. from 'Thing' -> 'Person'

        @param new_type_id: The ID of the new type that the new item should become
        @param split_on_incompatible: When converting between sibling types where
            existing properties are not applicable, we can create a new item,
            preserving the existing item and any properties specific to its type.
            An additional 'relatedTo' property will be used to link the two.

        @return: The item ID(s) of the item(s). When not splitting, the item ID will
                *not* change.
        """
        args = rebar.validated_args
        new_type_id = args.get('new_type_id')
        split_on_incompatible = args.get('split_on_incompatible')
        if split_on_incompatible:
            return {errors: ['Splitting not implemented']}, 400

        conn = get_connection(current_app)

        item = conn.get_item(item_id)
        if not item:
            return {'errors': ["Item not found"]}, 404

        new_item_type = conn.get_type(new_type_id)
        if not new_item_type:
            return {'errors': ["New item type not found"]}, 404

        try:
            conn.retype_item(item, new_item_type)
        except Exception as e:
            traceback.print_exc()
            return {'errors': ['Failed to retype item']}, 500



    @registry.handles(
            rule='/items/<item_id>',
            method='PATCH',
            request_body_schema=PatchItemSchema(),
            marshal_schema={
                200: PatchItemResponseSchema(),
                400: PatchItemResponseSchema(),
                404: PatchItemResponseSchema(),
                500: PatchItemResponseSchema(),
            }
    )
    def update_item(item_id):
        """
        Update an item, given a set of changes

        # Examples:

        Add a property to an existing item:
        [ { op: "ADD", property_id: "relatedTo", value: "..." } ]

        Change a property
        [ { op: "REPLACE", property_id: "name", value: "New Name" } ]

        Remove a single property
        [ { op: "DELETE", property_id: "age", value: "27" } ]

        Remove ALL properties by name
        [ { op: "DELETE", property_id: "relatedTo" } ]

        # Invalid operations

        ## Adding or removing the name of an item (cardinality exactly 1)
        [ { op: "ADD", property: "name" } ]
        [ { op: "DELETE", property: "name" } ]

        """

        changes = rebar.validated_body['changes']


        item = None
        try:
            conn = get_connection(current_app)
            item = conn.get_item(item_id)
        except Exception as e:
            current_app.logger.error(e)
            return { "errors": [ "Unable to update item" ]}, 500

        if not item:
            raise err.NotFound()

        ## Process additions
        for change in changes:
            try:
                op = change['op'].strip().lower() 
                if op == 'add':
                    prop = conn.get_property(change['property_id'])
                    if not prop:
                        raise err.InvalidPropertyError(f"Invalid Property: {prop}")
                    prop.value = change['value']
                        
                    conn.add_property_to_item(item, prop)
                elif op == 'replace':
                    # prop = conn.get_property(change['property_id'])
                    # prop.value = change['value']
                    # import pdb; pdb.set_trace()
                    pass
                elif op == 'delete':
                    prop = conn.get_property(change['property_id'])
                    invalid_deletion = ['name', 'created', 'type']
                    if prop.property_id in invalid_deletion or not prop: 
                        raise err.InvalidPropertyError(f"Invalid Property: {prop}")
                    prop.value = change['value']
                    # Only pass value if truthy
                    conn.delete_property_from_item(item, prop)

            except err.InvalidPropertyError as e:
                return { "errors": [str(e)] }, 400
            except Exception as e:
                current_app.logger.error(traceback.format_exc())
                return { "errors": [ "Server Error" ] }, 500



        # conn.delete_item(item_id)
        return { "errors": []}, 200



