class LtpItem():
    '''Class for a single "Item" object'''
    name: str
    itemType: str
    id: str = ""
    created: str = ""
    properties = []
    def __init__(self, name, itemType, id=None, created=None):
        self.name = name
        self.id = id
        self.itemType = itemType
        self.created = created

class LtpType():
    '''Class for a single "Type" object'''
    name: str
    id: str = ""
    description: str = ""
    created: str = ""
    properties = []
    def __init__(self, name, description, created="", id=None):
        self.name = name
        self.description = description
        self.id = id
        self.created = created

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


