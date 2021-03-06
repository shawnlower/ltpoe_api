from marshmallow import fields, Schema, validate

class MappingSchema(Schema):
    # e.g. schema.org/
    ontology = fields.String()
    # e.g. http://schema.org/
    uri = fields.String()
    # Property or Class
    rdf_type = fields.String()
    name = fields.String()
    # exactMatch, related, relatedProperty
    mapping_type = fields.String()

class PropertyValueSchema(Schema):
    id = fields.String()
    name = fields.String()
    # description = fields.String()
    value = fields.String()
    data_type = fields.String()

class PropertySchema(Schema):
    property_id = fields.String()
    name = fields.String()
    description = fields.String()
    data_type = fields.String()
    property_range = fields.List(fields.String)
    property_domain = fields.List(fields.String)
    value = fields.String()

class TypeSchema(Schema):
    type_id = fields.String()
    name = fields.String()
    description = fields.String()
    properties = fields.Nested(PropertySchema, many=True)

class ItemSchema(Schema):
    item_id = fields.String()
    name = fields.String()
    item_type = fields.String()
    properties = fields.Nested(PropertySchema, many=True)


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
    properties = fields.Nested(PropertyValueSchema, many=True, required=False)

class CreateTypeSchema(Schema):
    name = fields.String()
    description = fields.String(required=False)

class ChangeSchema(Schema):
    op = fields.String(required=True,
            validate=validate.OneOf(["add", "replace", "delete"]))
    property_id = fields.String(required=True)
    value = fields.String(required=True)

class PatchItemSchema(Schema):
    changes = fields.Nested(ChangeSchema, many=True, required=True)

##############################################################################
# Outgoing response schemas
##############################################################################

class CreateItemResponseSchema(Schema):
    item = fields.Nested(ItemSchema)
    errors = fields.String(many=True)

class DeleteItemResponseSchema(Schema):
    item = fields.Nested(ItemSchema)
    errors = fields.String(many = True)

class PatchItemResponseSchema(Schema):
    item = fields.Nested(ItemSchema)
    errors = fields.String(many = True)

class GetConfigResponseSchema(Schema):
    """
    Response for a config request
    """
    namespace = fields.String()

class GetMappingsResponseSchema(Schema):
    """
    Response for a 'mapping'
    """
    resource = fields.String()
    mappings = fields.Nested(MappingSchema, many=True)
    # more = fields.Boolean()
    results = fields.Integer()

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
    data = fields.Nested(ItemSchema)

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
    all_properties = fields.Boolean(required=False)
    offset = fields.Integer(required=False)
    item_type_id = fields.String(required=False)
    query = fields.String(required=False)

class GetTypesQueryStringSchema(Schema):
    max_results = fields.Integer(required=False)
    offset = fields.Integer(required=False)
    parent = fields.String(required=False)
    all_properties = fields.Boolean(required=False)

class RetypeItemQueryStringSchema(Schema):
    new_type_id = fields.String(required=True)
    split_on_incompatible = fields.Boolean(default=False, required=False)

# Get a SINGLE item
class GetItemQueryStringSchema(Schema):
    all_properties = fields.Boolean(required=False)

# Get a SINGLE type
class GetTypeQueryStringSchema(Schema):
    all_properties = fields.Boolean(required=False)


