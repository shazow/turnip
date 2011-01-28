from turnip.tests import TestModel, model, Session

from turnip.worker import Worker

from datetime import datetime, timedelta

class TestTasks(TestModel):
    def test_completion(self):
        w = Worker()

        t = model.Task.create(method='foo')
        Session.commit()

        t = model.Task.next()

        self.assertTrue(t)
        self.assertEqual(t.state, 'pending')

        t.start(w)
        self.assertEqual(t.state, 'started')

        t.complete(w)
        self.assertEqual(t.state, 'completed')

        t.start(w)
        t.retry(w)
        self.assertEqual(t.state, 'pending')

        t2 = t.create_recurring()
        self.assertFalse(t2)

    def test_recurring(self):
        now = datetime.now()
        nowish = now - timedelta(days=2)

        w = Worker()

        t = model.Task.create(method='foo', recurring_cron='0 0 * * *')
        Session.commit()

        t.time_created = nowish

        t.start(w)
        t.complete(w)
        t2 = t.create_recurring()

        self.assertTrue(t2)
        self.assertEqual(t2.time_wait_until.hour, 0)
        self.assertTrue(t2.time_wait_until > now)

    def test_delay_resource_group(self):
        model.Task.create(method='foo', resource_group='internal')
        model.Task.create(method='foo', resource_group='internal')
        model.Task.create(method='foo', resource_group='internal')
        Session.commit()

        q = Session.query(model.Task).filter_by(state='pending').filter(model.Task.time_wait_until<=datetime.now())
        self.assertEqual(q.count(), 3)

        model.Task.delay_resource_group('foo', timedelta(hours=2))
        Session.commit()

        self.assertEqual(q.count(), 3)

        model.Task.delay_resource_group('internal', timedelta(hours=2))
        Session.commit()

        self.assertEqual(q.count(), 0)
