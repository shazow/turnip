# Example 1:

def print_string(s, **params):
    print s

def rebuild(worker):
    from turnip import model
    Session = model.Session

    model.Task.create(method='tasks:print_string', params={'s': 'Hello World'})
    model.Task.create(method='tasks:print_string', params={'s': 'Hello World 2'})
    model.Task.create(method='tasks:print_string', params={'s': 'Hello World 3'})
    Session.commit()


# Example 2:

CACHE = {}

def print_from_cache(key, **params):
    print CACHE.get(key)

def setup_cache():
    CACHE[42] = 'What is the answer to life, the universe, and everything?'

def rebuild_cache_tasks(worker):
    from turnip import model
    Session = model.Session

    # Create an always-recurring task
    model.Task.create(method='tasks:print_from_cache', params={'key': 42}, recurring_cron='* * * * *')
    Session.commit()


# More useful examples

def setup_pylons(config_file='development.ini'):
    from myproject.config import load_environment
    from paste.deploy import appconfig

    conf = appconfig('config:' + config_file, relative_to='.')
    config = load_environment(conf.global_conf, conf.local_conf)

    import pylons
    pylons.config = config
