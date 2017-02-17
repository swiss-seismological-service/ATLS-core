# -*- encoding: utf-8 -*-
"""
The session is used by SQLAlchemy to persist event objects to the database.

All objects that need to be persisted should inherit from the declarative base
provided by :mod:`ormbase`.

Copyright (C) 2013-2017, ETH Zurich - Swiss Seismological Service SED

"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ormbase import OrmBase


def load_db(path):
    engine = create_engine(path)
    OrmBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return engine, session
