class LtpItem():
    '''Class for a single "Item" object'''
    name: str
    itemType: str
    id: str = ""
    created: str = ""
    properties = []
    def __init__(self, name, itemType, item_id=None, created=None, 
            namespace=None):
        self.name = name
        self.id = id
        self.itemType = itemType
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
    name: str
    id: str = ""
    value: str = ""
    datatype: str = ""
    def __init__(self, name, id=None, value=None, description=None, datatype=None):
        self.name = name
        self.id = id
        self.value = value
        self.description = description
        self.datatype = datatype

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


