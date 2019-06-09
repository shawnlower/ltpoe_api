from flask_rebar.errors import *

class InvalidProperty(ValueError):
    def __init__(self, msg=None):
        if not msg:
            self.msg = "Property object is invalid or incomplete."
        else:
            self.msg = msg
        super(InvalidPropertyError, self).__init__(self.msg)

class InvalidConfiguration(SyntaxError):
    def __init__(self, msg=None):
        if not msg:
            self.msg = "Application configuration is invalid"
        else:
            self.msg = msg
        super(SyntaxError, self).__init__(self.msg)

