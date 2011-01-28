from unittest import TestCase

__all__ = ['TestModel', 'model', 'Session']

from turnip import model
Session = model.Session

from sqlalchemy import create_engine

engine = create_engine("sqlite:///:memory:")
model.init_model(engine)

class TestModel(TestCase):

    def setUp(self):
        model.metadata.create_all(bind=Session.bind)

    def tearDown(self):
        Session.rollback()
        model.metadata.drop_all(bind=Session.bind)
