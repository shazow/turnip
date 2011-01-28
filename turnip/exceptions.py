class TaskException(Exception):
    def __init__(self, message):
        self.message = message

class TaskDelayResource(TaskException):
    def __init__(self, message, resource, delay=60*60):
        self.message = message
        self.resource = resource
        self.delay = delay

class TaskError(TaskException):
    pass

class TaskAbort(TaskException):
    pass

