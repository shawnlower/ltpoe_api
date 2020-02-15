from flask_rebar.errors import *

class InvalidItemError(ValueError):
    def __init__(self, msg=None):
        if not msg:
            self.msg = "Invalid item"
        else:
            self.msg = msg
        super(InvalidItemError, self).__init__(self.msg)

class InvalidPropertyError(ValueError):
    def __init__(self, msg=None):
        if not msg:
            self.msg = "Property object is invalid or incomplete."
        else:
            self.msg = msg
        super(InvalidPropertyError, self).__init__(self.msg)

class InvalidTypeError(ValueError):
    def __init__(self, msg=None):
        if not msg:
            self.msg = "Type object is invalid or incomplete."
        else:
            self.msg = msg
        super(InvalidTypeError, self).__init__(self.msg)

class InvalidConfigurationError(SyntaxError):
    def __init__(self, msg=None):
        if not msg:
            self.msg = "Application configuration is invalid"
        else:
            self.msg = msg
        super(InvalidConfigurationError, self).__init__(self.msg)

class NotFoundError(ValueError):
    def __init__(self, msg=None):
        if not msg:
            self.msg = "Not found"
        else:
            self.msg = msg
        super(NotFoundError, self).__init__(self.msg)
