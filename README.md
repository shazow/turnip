# Turnip

Like [celeryq](http://celeryq.org/) but tastier.

## Tasty

The goal is to be simple, small, and self-contained.

* Built on SQLAlchemy. Everything is contained in one table named ``turnip_task``. This means you can mess around with an SQLite storage during development, and push it out with PostgreSQL in production. Less moving pieces.
* Supports recurring tasks with a cron-like scheduling syntax and and followup tasks.
* Multiple workers should work in theory (untested, may need some transaction tweaking before it'll work reliably).


## Usage

    Usage: turnip --engine=ENGINE COMMAND [ARGS ...]

    Turnip task management. Tastier than celery.

    Commands:

        run
            Process tasks forever.

        prune
            Delete old tasks with states 'complete' or 'error'.

        revive
            Set 'started' tasks to 'pending'.

        rebuild [FN]
            Delete 'pending' tasks (and run FN if given).

        list
            List tasks.


    Options:
      -h, --help            show this help message and exit
      -v, --verbose         Enable verbose output. Use twice to enable debug
                            output.
      -e ENGINE, --engine=ENGINE
                            Database engine to use where tasks are stored.


## Schema

    class Task(BaseModel):
        __tablename__ = 'turnip_task'

        id = Column(types.Integer, primary_key=True)
        time_created = Column(types.DateTime, default=datetime.now, nullable=False)
        time_updated = Column(types.DateTime, onupdate=datetime.now)

        time_wait_until = Column(types.DateTime, default=datetime.now, nullable=False)
        seconds_elapsed = Column(types.Float)

        # Tag tasks that depend on a specific resource so they can be queried 
        # Example: An error from a 'twitter-api' tag would trigger a 1hr delay on all pending tasks of that group.
        resource_group = Column(types.String(32))

        method = Column(types.String(32), nullable=False)
        params = Column(types.PickleType, default=dict, nullable=False)

        lock_key = Column(types.String(32))

        recurring_cron = Column(types.String(128)) # Cron-like string for recurring. If not set, wont recur.

        parent_task_id = Column(types.Integer, ForeignKey('task.id'))
        parent_task = orm.relationship('Task', remote_side=id)
        parent_type = Column(mytypes.Enum(['master', 'retry', 'recurring']), default='master', nullable=False)

        state = Column(mytypes.Enum(['pending', 'started', 'completed', 'failed']), default='pending', nullable=False, index=True)
