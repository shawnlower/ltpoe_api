from marshmallow import fields, Schema

class TypeSchema(Schema):
    iri = fields.String()
    name = fields.String()
    description = fields.String()

class PropertySchema(Schema):
    iri = fields.String()
    name = fields.String()
    description = fields.String()
    datatype = fields.String()

##############################################################################
# Request schemas
##############################################################################

class CreateTypeSchema(Schema):
    name = fields.String()
    description = fields.String(required=False)

##############################################################################
# Outgoing response schemas
##############################################################################

class GetTypesResponseSchema(Schema):
    data = fields.Nested(TypeSchema, many=True)
    more = fields.Boolean()
    results = fields.Integer()

class GetTypeResponseSchema(Schema):
    metadata = fields.Nested(TypeSchema)
    properties = fields.Nested(PropertySchema, many=True)
    num_properties = fields.Integer()

##############################################################################
# Query strings
##############################################################################

class GetTypesQueryStringSchema(Schema):
    max_results = fields.Integer(required=False)
    offset = fields.Integer(required=False)
    parent = fields.String(required=False)

# Get a SINGLE type
class GetTypeQueryStringSchema(Schema):
    all_properties = fields.Boolean(required=False)


