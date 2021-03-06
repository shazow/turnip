import uuid
from datetime import datetime, timedelta
import time
import traceback

from turnip.exceptions import TaskError, TaskDelayResource, TaskAbort
from turnip.util import get_task_method
from turnip import model
Session = model.Session

from sqlalchemy.exc import SQLAlchemyError

import logging
log = logging.getLogger('turnip')

LOOP_SLEEP = 0
LOOP_CONTINUE = 1

def delta_seconds(t1, t2):
    return time.mktime(t2.timetuple()) - time.mktime(t1.timetuple())

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

        max_jobs = params.get('max_jobs')

        while True:
            count = 0
            while self.do_task() == LOOP_CONTINUE:
                count += 1

                if max_jobs and count > max_jobs:
                    self.log.info("Shutting down due to max_jobs")
                    return

            sleep_time = interval
            t = model.Task.next(or_upcoming=True)
            if t:
                sleep_time = min(sleep_time, delta_seconds(datetime.now(), t.time_wait_until))

            self.log.info("Completed {0} tasks in this cycle.".format(count))

            if params.get('one_cycle') and count:
                self.log.info("Shutting down due to one_cycle.")
                return

            if sleep_time <= 0:
                continue

            self.log.info("Sleeping {0} seconds until next cycle.".format(sleep_time))

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
            return LOOP_SLEEP

        t.start(self)
        Session.commit()

        if not t.check_lock(self):
            # Another worker got the task, abort.
            return LOOP_CONTINUE

        # Perform task
        self.log.info("Starting task: {0}".format(t))

        fn = get_task_method(t.method)
        try:
            r = fn(task_id=t.id, **t.params)

            self.log.info("Task completed: {0}".format(t))
            t.complete(self)

        except TaskDelayResource, e:
            new = t.retry(self, delay=e.delay)
            self.log.warn("Task error, will retry in {0} seconds: {1}".format(e.delay, e.message))
            resource = e.resource or t.resource_group
            if resource:
                self.log.warn("Delaying resource group by {0} seconds: {1}".format(e.delay, resource))
                model.Task.delay_resource_group(resource, timedelta(seconds=e.delay))

        except TaskAbort, e:
            self.log.warn("Aborting task: {0}".format(e.message))
            t.fail(self)

        except Exception, e:
            Session.rollback()

            self.log.error("Unexpected task error, will retry in an hour: {0} - {1}".format(repr(e), str(e)))
            traceback.print_exc()
            new = t.retry(self, delay=60*60)

        Session.commit()

        if t.state != 'completed':
            return LOOP_CONTINUE

        if t.recurring_cron:
            new = t.create_recurring()

        Session.commit()
        Session.remove()

        return LOOP_CONTINUE


