from turnip.model.meta import Session, metadata
from turnip.model.objects import *

def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    Session.configure(bind=engine)
