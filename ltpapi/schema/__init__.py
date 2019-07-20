from marshmallow import fields, Schema

class ItemSchema(Schema):
    item_id = fields.String()
    name = fields.String()
    item_type = fields.String()

class TypeSchema(Schema):
    type_id = fields.String()
    name = fields.String()
    description = fields.String()

class PropertyValueSchema(Schema):
    id = fields.String()
    name = fields.String()
    description = fields.String()
    value = fields.String()
    data_type = fields.String()

class PropertySchema(Schema):
    property_id = fields.String()
    name = fields.String()
    description = fields.String()
    data_type = fields.String()
    property_range = fields.List(fields.String)
    property_domain = fields.List(fields.String)


class CreatePropertySchema(Schema):
    name = fields.String(required=True)
    description = fields.String(required=True)
    item_types = fields.List(fields.String, required=True)
    data_types = fields.List(fields.String, required=True)

##############################################################################
# Request schemas
##############################################################################

class CreateItemSchema(Schema):
    name = fields.String(required=True)
    item_type = fields.String(required=True)

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
    item_id = fields.String()
    item_type = fields.String()
    properties = fields.Dict()
    num_properties = fields.Integer()

class GetPropertiesResponseSchema(Schema):
    metadata = fields.Nested(PropertySchema)
    data = fields.Nested(PropertySchema, many=True)
    num_properties = fields.Integer()

class GetPropertyResponseSchema(Schema):
    data = fields.Nested(PropertySchema)

##############################################################################
# Query strings
##############################################################################

class GetPropertiesQueryStringSchema(Schema):
    max_results = fields.Integer(required=False)
    offset = fields.Integer(required=False)

class GetItemsQueryStringSchema(Schema):
    max_results = fields.Integer(required=False)
    item_type_id = fields.String(required=False)
    offset = fields.Integer(required=False)

class GetTypesQueryStringSchema(Schema):
    max_results = fields.Integer(required=False)
    offset = fields.Integer(required=False)
    parent = fields.String(required=False)

# Get a SINGLE item
class GetItemQueryStringSchema(Schema):
    item_type_id = fields.String(required=True)
    all_properties = fields.Boolean(required=False)

# Get a SINGLE type
class GetTypeQueryStringSchema(Schema):
    all_properties = fields.Boolean(required=False)


