
class ParamError(Exception):
    def __init__(self):
        self.message = 'No location codes provided'


class MissingEnvVar(Exception):
    
    def __init__(self, var):
        self.message = 'Missing environment variable: ' + var
