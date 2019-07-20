class LtpItem():
    '''Class for a single "Item" object'''
    name: str
    item_type: str
    item_id: str = ""
    created: str = ""
    properties = []
    def __init__(self, name, item_type, item_id=None, created=None, 
            namespace=None):
        self.name = name
        self.item_id = item_id
        self.item_type = item_type
        self.created = created

class LtpType():
    '''Class for a single "Type" object'''
    name: str
    description: str = ""
    created: str = ""
    properties = []
    def __init__(self, name, description, namespace, created=None,
            type_id=None):
        self.name = name
        self.namespace = namespace
        self.description = description
        self.type_id = type_id
        self.created = created

    def get_uri(self):
        return self.namespace.term(self.type_id)


class LtpProperty():
    '''Class for a single "Property" object'''
    def __init__(self, name, namespace, property_id=None, value=None, description=None,
            datatype=None, property_range=None, property_domain=None):
        self.name = name
        self.property_id = id
        self.value = value
        self.namespace = namespace
        self.description = description
        self.datatype = datatype
        self.property_range = property_range
        self.property_domain = property_domain

    def get_uri(self):
        return self.namespace.term(self.property_id)

    def validate(self):
        """Ensure the property is complete and consistent.

        Specifically:
        - Required fields: name, description
        - Datatype specifies a valid type
        - id exists
        """
        required = ['name', 'description']
        missing  = [k for k in required if not getattr(self, k)]
        if missing:
            raise err.InvalidProperty('Missing keys {}'.format(str(missing)))

        raise err.NotImplemented


