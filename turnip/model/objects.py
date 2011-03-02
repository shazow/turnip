from turnip.model.meta import Session, BaseModel
from turnip.model import types as mytypes

from sqlalchemy import orm, types, Column, Index, ForeignKey, and_
from datetime import datetime, timedelta
import time
from croniter import croniter

__all__ = [
    'Task',
]

# Task management

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

    # A ``method`` is a Python object path to a callable that takes ``params``.
    method = Column(types.Text, nullable=False)
    params = Column(types.PickleType, default=dict, nullable=False)

    # Random byte string (like a uuid)
    lock_key = Column(types.LargeBinary(16))

    recurring_cron = Column(types.String(128)) # Cron-like string for recurring. If not set, wont recur.

    # Set when the current task is related to another task.
    parent_task_id = Column(types.Integer)
    parent_task = orm.relationship('Task', remote_side=id)
    parent_type = Column(mytypes.Enum(['master', 'retry', 'recurring']), default='master', nullable=False)

    state = Column(mytypes.Enum(['pending', 'started', 'completed', 'failed', 'retried']), default='pending', nullable=False, index=True)

    def __str__(self):
        return "%d:%s(%r)" % (self.id, self.method, self.params)

    @staticmethod
    def delay_resource_group(resource_group, delta=None):
        # Make sure all tasks of given resource_group are scheduled for no sooner than now+delta.
        affected_tasks = Session.query(Task).filter(and_(Task.time_wait_until > (datetime.now() - delta), Task.state<'completed', Task.resource_group==resource_group))
        for t in affected_tasks:
            t.time_wait_until += delta


    @staticmethod
    def create_from_time(delta=None, now=None, resolution='hour', **kw):
        if not now:
            now = datetime.now()

        if not delta:
            return Task.create(time_wait_until=now, **kw)

        resolutions = ['year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond']
        if resolution not in resolutions:
            raise KeyError("Resolution is not valid: {0}".format(resolution))

        t = now + delta
        args = []
        for r in resolutions:
            args += [getattr(t, r)]
            if r == resolution:
                break

        return Task.create(time_wait_until=datetime(*args), **kw)

    @staticmethod
    def next(or_upcoming=False):
        q = Session.query(Task).filter_by(state='pending')
        if not or_upcoming:
            q = q.filter(Task.time_wait_until<=datetime.now())

        q.order_by(Task.time_wait_until.asc())
        return q.first()

    def create_recurring(self):
        if not self.recurring_cron:
            return

        now = datetime.now()
        cron = croniter(self.recurring_cron, self.time_created)

        time_next_task = cron.get_next(datetime)
        while time_next_task < now:
            time_next_task = cron.get_next(datetime)

        t = Task.create(time_wait_until=time_next_task, resource_group=self.resource_group,
                method=self.method, params=self.params, recurring_cron=self.recurring_cron,
                parent_task_id=self.id, parent_type='recurring')
        return t

    def start(self, worker):
        self.state = 'started'
        self.lock_key = worker.lock
        self._seconds_started = time.time()

    def retry(self, worker, delay=0):
        self.state = 'retried'
        time_retry = time_wait_until = datetime.now() + timedelta(seconds=delay)

        t = Task.create(time_wait_until=time_retry, resource_group=self.resource_group,
                method=self.method, params=self.params, recurring_cron=self.recurring_cron,
                parent_task_id=self.id, parent_type='retry')

        return t

    def complete(self, worker):
        if not self.check_lock(worker):
            raise AssertionError("Invalid lock for complete_task {0}: {1}".format(self.id, worker.lock))

        self.seconds_elapsed = time.time() - self._seconds_started
        self.state = 'completed'

    def fail(self, worker):
        if not self.check_lock(worker):
            raise AssertionError("Invalid lock for complete_task {0}: {1}".format(self.id, worker.lock))

        self.seconds_elapsed = time.time() - self._seconds_started
        self.state = 'failed'


    def check_lock(self, worker):
        return self.lock_key == worker.lock


Index('turnip_task_discover_idx',
      Task.state,
      Task.time_wait_until)
