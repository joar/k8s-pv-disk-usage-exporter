class LoggableError(Exception):
    def __init__(self, message=None, **data):
        self.message = message,
        self.data = data

    def __structlog__(self):
        loggable = {
            'error': self.__class__.__name__,
            'data': self.data,
        }
        return loggable


class ResourceNotFound(LoggableError):
    pass
