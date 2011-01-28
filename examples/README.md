# Example 1: Simple print.

First we tell turnip which database to use. This is where tasks will be inserted into and read from.

    $ export TURNIP_ENGINE="sqlite:///$PWD/turnip.db"

Now we insert some tasks. We defined a ``rebuild`` method inside of ``tasks.py`` of this directory.

This is a path of the form ``path.to.module.Object:callable``. In this case, the module is ``tasks`` and the callable within it is ``rebuild``.

    $ turnip rebuild tasks:rebuild

We can see that a database was created, and we can run ``list`` on it.

    $ ls -lah turnip.db
    -rw-r--r--  1 me  staff   8.0K Jan 27 22:43 turnip.db

    $ turnip list
    -- Summaries --
    Pending:	 3
    Started:	 0
    Completed:	 0
    Failed: 	 0

Now lets run the tasks.

    $ turnip run
    Hello World
    Hello World 2
    Hello World 3
    ^C

In this case, each task was to print a string. Very simple.

Next we'll learn how to define an environment that each worker needs to setup before running tasks.

# Example 2: Custom worker environment

Let's start fresh.

    $ rm turnip.db
    $ export TURNIP_ENGINE="sqlite:///$PWD/turnip.db"

Now lets build a task that prints a value from a cached dict. We'll set the values of the dict from a ``setup`` function that will get run upon instantiation of the worker.

    $ turnip rebuild tasks:rebuild_cache_tasks

If you look into ``tasks.py`` you'll see that rebuild_cache_tasks generates one recurring tasks.

    CACHE = {}

    def print_from_cache(key, **params):
        print CACHE.get(key)

    def rebuild_cache_tasks(worker):
        # ...
        model.Task.create(method='tasks:print_from_cache', params={'key': 42}, recurring_cron='* * * * *')

Let's try it:

    $ turnip run
    None
    ^C

The cache is empty. We have a ``setup_cache`` method which pre-populates the cache.

    def setup_cache():
        CACHE[42] = 'What is the answer to life, the universe, and everything?'

Let's try it with the setup method:

    $ turnip --setup tasks:setup_cache run
    What is the answer to life, the universe, and everything?

There we go.
