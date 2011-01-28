def get_task_method(path):
    # FIXME: There's a builtin for this in Python 2.7
    module, obj = path.split(':', 1)
    o = __import__(module, fromlist=[obj])
    return getattr(o, obj)
