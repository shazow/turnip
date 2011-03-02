from turnip.util import get_task_method
from turnip import model
Session = model.Session

from sqlalchemy import and_
from datetime import datetime, timedelta

import logging
log = logging.getLogger('turnip')

__all__ = ['run', 'prune', 'rebuild', 'revive', 'list']

def run(worker, **params):
    worker.run(**params)


def revive(worker, **params):
    t = model.Task.__table__
    q = t.update().where(and_(t.c.state=='started')).values(state='pending', lock_key=None)
    Session.execute(q).close()
    Session.commit()


def prune(worker, **params):
    t = model.Task.__table__
    q = t.delete().where(and_(t.c.time_wait_until < (datetime.now() - timedelta(weeks=1)), t.c.state>='completed'))
    Session.execute(q).close()
    Session.commit()


def rebuild(worker, **params):
    method = params.get('method')
    if not method:
        log.error("No rebuild method given.")

    fn = get_task_method(method)
    if not fn:
        log.error("Rebuild method not found: %s" % method)

    log.debug("Deleting pending tasks.")
    t = model.Task.__table__
    q = t.delete().where(t.c.state<'completed')
    Session.execute(q).close()
    Session.commit()

    fn(worker)


def list(worker, **params):
    state = params.get('state')

    if state:
        q = Session.query(model.Task).filter_by(state=state)
        for task in q:
            print q

    print "-- Summaries --"
    print "Pending:\t %d" % Session.query(model.Task).filter_by(state='pending').count()
    print "Started:\t %d" % Session.query(model.Task).filter_by(state='started').count()
    print "Completed:\t %d" % Session.query(model.Task).filter_by(state='completed').count()
    print "Failed: \t %d" % Session.query(model.Task).filter_by(state='failed').count()
