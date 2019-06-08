from flask_rebar.errors import *

class InvalidProperty(ValueError):
    def __init__(self, msg=None):
        if not msg:
            self.msg = "Property object is invalid or incomplete."
        super(InvalidPropertyError, self).__init__(self.msg)

