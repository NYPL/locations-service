
class ParamError(Exception):
    def __init__(self, message='No location codes provided'):
        self.message = message


class MissingEnvVar(Exception):
    def __init__(self, var):
        self.message = 'Missing environment variable: ' + var


class RefineryApiError(Exception):
    def __init__(self, message=None):
        self.message = message
