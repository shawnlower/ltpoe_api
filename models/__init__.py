from marshmallow import fields, Schema

class ItemSchema(Schema):
    id = fields.String()
    name = fields.String()
    itemType = fields.String()

class TypeSchema(Schema):
    id = fields.String()
    name = fields.String()
    description = fields.String()

class PropertyValueSchema(Schema):
    iri = fields.String()
    name = fields.String()
    description = fields.String()
    value = fields.String()
    datatype = fields.String()

class PropertySchema(Schema):
    iri = fields.String()
    name = fields.String()
    description = fields.String()
    datatype = fields.String()

##############################################################################
# Request schemas
##############################################################################

class CreateItemSchema(Schema):
    name = fields.String()
    itemType = fields.String()

class CreateTypeSchema(Schema):
    name = fields.String()
    description = fields.String(required=False)

##############################################################################
# Outgoing response schemas
##############################################################################

class CreateItemResponseSchema(Schema):
    item = fields.Nested(ItemSchema)

class GetTypesResponseSchema(Schema):
    data = fields.Nested(TypeSchema, many=True)
    more = fields.Boolean()
    results = fields.Integer()

class GetTypeResponseSchema(Schema):
    metadata = fields.Nested(TypeSchema)
    properties = fields.Nested(PropertySchema, many=True)
    num_properties = fields.Integer()

class GetItemsResponseSchema(Schema):
    data = fields.Nested(ItemSchema, many=True)
    more = fields.Boolean()
    results = fields.Integer()

class GetItemResponseSchema(Schema):
    metadata = fields.Nested(ItemSchema)
    properties = fields.Nested(PropertyValueSchema, many=True)
    num_properties = fields.Integer()

class GetPropertiesResponseSchema(Schema):
    metadata = fields.Nested(PropertySchema)
    data = fields.Nested(PropertySchema, many=True)
    num_properties = fields.Integer()

##############################################################################
# Query strings
##############################################################################

class GetPropertiesQueryStringSchema(Schema):
    max_results = fields.Integer(required=False)
    offset = fields.Integer(required=False)

class GetItemsQueryStringSchema(Schema):
    itemTypeId = fields.String(required=True)
    max_results = fields.Integer(required=False)
    offset = fields.Integer(required=False)

class GetTypesQueryStringSchema(Schema):
    max_results = fields.Integer(required=False)
    offset = fields.Integer(required=False)
    parent = fields.String(required=False)

# Get a SINGLE item
class GetItemQueryStringSchema(Schema):
    all_properties = fields.Boolean(required=False)

# Get a SINGLE type
class GetTypeQueryStringSchema(Schema):
    all_properties = fields.Boolean(required=False)


