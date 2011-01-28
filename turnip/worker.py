import uuid
from datetime import datetime, timedelta
import time

from turnip.exceptions import TaskError, TaskDelayResource, TaskAbort
from turnip.util import get_task_method
from turnip import model
Session = model.Session

import logging
log = logging.getLogger('turnip')

class Worker(object):
    def __init__(self, lock=None):
        self.lock = lock or uuid.uuid1().get_bytes()
        self.log = logging.getLogger('turnip.worker')

    def __str__(self):
        return "<worker:{0}>".format(self.lock)

    def run(self, **params):
        """
        Start infinite do_task loop.

        :param interval: Number of seconds to wait between looking for new tasks. (Default: 3600)
        """

        interval = int(params.get('interval') or 3600)

        if interval < 60:
            raise ValueError("Interval must be at least 60 seconds.")

        while True:
            while self.do_task():
                pass
            sleep_time = interval
            t = model.Task.next(or_upcoming=True)
            if t:
                sleep_time = min(sleep_time, (t.time_wait_until - datetime.now()).seconds)
            self.log.info("task loop waiting {0} seconds...".format(sleep_time))
            try:
                time.sleep(sleep_time)
            except KeyboardInterrupt, e:
                log.warn("Aborting loop.")
                break


    def do_task(self, **params):
        """Perform the next ready task in the queue.
        """

        # Get next task and lock it.
        t = model.Task.next()
        if not t:
            self.log.info("No ready tasks found.")
            return False

        t.start(self)
        Session.commit()

        if not t.check_lock(self):
            # Another worker got the task, abort.
            return False

        # Perform task
        self.log.info("Starting task: {0}".format(t))

        fn = get_task_method(t.method)
        try:
            r = fn(task_id=t.id, **t.params)

            self.log.info("Task completed: {0}".format(t))
            t.complete(self)

        except TaskDelayResource, e:
            t.retry(self, delay=e.delay)
            self.log.warn("Task error, delaying resource group '{0}': {1}".format(e.resource, e.message))
            model.Task.delay_resource_group('twitterapi', timedelta(hours=1))

        except TaskAbort, e:
            self.log.warn("Aborting task: {0}".format(e.message))
            t.fail()
            Session.commit()
            return True

        except Exception, e:
            self.log.error("Unexpected task error, will retry later: {0}".format(repr(e)))
            t.retry(self, delay=60*24)

        Session.commit()

        if t.state != 'completed':
            return True

        if t.recurring_cron:
            new = t.create_recurring()

        Session.commit()

        return True


