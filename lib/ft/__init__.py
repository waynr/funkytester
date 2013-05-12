from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

session_factory = sessionmaker()
LogDBSession = scoped_session(session_factory)
Base = declarative_base()

def setup_logdb_engine(*args):
    engine = create_engine(*args)
    session_factory.configure(bind=engine)

import test
import platform
import device
import unittest
import event

__all__ = [
        test,
        platform,
        device,
        unittest,
        event,

        Base,
        LogDBSession,
        setup_logdb_engine,
        ]
