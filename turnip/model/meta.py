"""SQLAlchemy Metadata and Session object"""
from sqlalchemy import MetaData, select, bindparam, types
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.session import Session as SessionBase
from sqlalchemy.interfaces import ConnectionProxy

from datetime import datetime, date
import time

__all__ = ['Session', 'metadata', 'BaseModel']

Session = scoped_session(sessionmaker(expire_on_commit=False))
metadata = MetaData()
# Declarative base

from sqlalchemy.ext.declarative import declarative_base

class _Base(object):

    @classmethod
    def get(cls, id):
        return Session.query(cls).get(id)

    @classmethod
    def get_by(cls, **kw):
        return Session.query(cls).filter_by(**kw).first()

    @classmethod
    def get_or_create(cls, **kw):
        r = cls.get_by(**kw)
        if not r:
            r = cls(**kw)
            Session.add(r)

        return r

    @classmethod
    def create(cls, **kw):
        r = cls(**kw)
        Session.add(r)
        return r

    def delete(self):
        Session.delete(self)

BaseModel = declarative_base(metadata=metadata, cls=_Base)
