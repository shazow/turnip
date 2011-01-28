# Examples

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

**TODO**: ...
