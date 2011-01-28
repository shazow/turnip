def rebuild():
    from turnip import model
    Session = model.Session

    model.Task.create(method='tasks:print_string', params={'s': 'Hello World'})
    model.Task.create(method='tasks:print_string', params={'s': 'Hello World 2'})
    model.Task.create(method='tasks:print_string', params={'s': 'Hello World 3'})
    Session.commit()

def print_string(s, **params):
    print s
