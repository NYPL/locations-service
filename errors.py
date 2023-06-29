
class ParamError(Exception):
    def __init__(self):
        self.message = 'No location codes provided'
