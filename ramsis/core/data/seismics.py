# -*- encoding: utf-8 -*-
"""
History of seismic events

"""

import logging
import traceback

from PyQt4 import QtCore
from sqlalchemy import Column, Table
from sqlalchemy import Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ormbase import OrmBase, DeclarativeQObjectMeta

from core.data.geometry import Point

_catalogs_events_table = Table('catalogs_events', OrmBase.metadata,
                               Column('seismic_catalogs_id', Integer,
                                      ForeignKey('seismic_catalogs.id')),
                               Column('seismic_events_id', Integer,
                                      ForeignKey('seismic_events.id')))


class SeismicCatalog(QtCore.QObject, OrmBase):
    """
    Provides a history of seismic events and functions to read and write them
    from/to a persistent store. The class uses Qt signals to signal changes.

    """
    __metaclass__ = DeclarativeQObjectMeta

    # region ORM Declarations
    __tablename__ = 'seismic_catalogs'
    id = Column(Integer, primary_key=True)
    catalog_date = Column(DateTime)
    # SeismicEvent relation (we own them)
    seismic_events = relationship('SeismicEvent',
                                  order_by='SeismicEvent.date_time',
                                  secondary=_catalogs_events_table,
                                  back_populates='seismic_catalog')
    # Parents
    # ...Project relation
    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship('Project', back_populates='seismic_catalog')
    # ...ForecastInput relation
    forecast_input_id = Column(Integer, ForeignKey('forecast_inputs.id'))
    forecast_input = relationship('ForecastInput',
                                  back_populates='input_catalog')
    # ...SkillTest relation
    skill_test_id = Column(Integer, ForeignKey('skill_tests.id'))
    skill_test = relationship('SkillTest',
                              back_populates='reference_catalog')
    # endregion

    def __init__(self, store):
        QtCore.QObject.__init__(self)
        self.store = store
        self._logger = logging.getLogger(__name__)

    def import_events(self, importer, timerange=None):
        """
        Imports seismic events from a csv file by using an EventImporter

        The EventImporter must return the following fields (which must thus
        be present in the csv file)

        x: x coordinate [m]
        y: y coordinate [m]
        depth: depth [m], positive downwards
        mag: magnitude

        :param importer: an EventImporter object
        :type importer: EventImporter
        :param timerange: limit import to specified time range
        :type timerange: DateTime tuple

        """
        events = []
        try:
            for date, fields in importer:
                location = Point(float(fields['x']),
                                 float(fields['y']),
                                 float(fields['depth']))
                event = SeismicEvent(date, float(fields['mag']), location)
                events.append(event)
        except:
            self._logger.error('Failed to import seismic events. Make sure '
                               'the .csv file contains x, y, depth, and mag '
                               'fields and that the date field has the format '
                               'dd.mm.yyyyTHH:MM:SS. The original error was ' +
                               traceback.format_exc())
        else:
            predicate = None
            if timerange:
                predicate = (self.entity.date_time >= timerange[0],
                             self.entity.date_time <= timerange[1])
            self.store.purge_entity(self.entity, predicate)
            self.store.add(events)
            self._logger.info('Imported {} seismic events.'.format(
                len(events)))
            self.reload_from_store()
            self._emit_change_signal({})

    def events_before(self, end_date, mc=0):
        """ Returns all events >mc before and including *end_date* """
        predicate = (SeismicEvent.date_time <= end_date,
                     SeismicEvent.magnitude > mc)
        events = self.store.read_all(SeismicEvent, predicate=predicate,
                                     order="date_time")
        return events

    def latest_event(self, time=None):
        """
        Returns the latest event before time *time*

        If time constraint is not given, the latest event in the entire history
        is returned.

        :param time: time constraint for latest event
        :type time: datetime

        """
        predicate = None
        if time:
            predicate = SeismicEvent.date_time < time
        events = self.store.read_all(SeismicEvent, predicate=predicate,
                                     order="date_time")
        return events[-1] if len(events) > 0 else None

    def clear_events(self):
        """
        Clear all seismic events from the database

        """
        self.store.purge_entity(self.entity)
        self._logger.info('Cleared all seismic events.')
        self.reload_from_store()
        self._emit_change_signal({})

    def copy(self):
        """ Returns a new copy of itself """

        arguments = {}
        for name, column in self.__mapper__.columns.items():
            if not (column.primary_key or column.unique):
                arguments[name] = getattr(self, name)
        copy = self.__class__(self.store)
        for item in arguments.items():
            setattr(copy, *item)
        return copy

    def __getitem__(self, item):
        events = self.store.read_all(SeismicEvent)
        if len(events) == 0:
            return None
        else:
            return events[item]

    def __len__(self):
        events = self.store.read_all(SeismicEvent)
        return len(events)


class SeismicEvent(OrmBase):
    """
    Represents a seismic event

    A seismic event consists of at least one magnitude and one origin. Multiple
    magnitudes and origins can be present for a single event. In that case, the
    members *magnitude* and *origin* will point to the preferred magnitude and
    origin respectively.

    """

    # region ORM declarations
    __tablename__ = 'seismic_events'
    id = Column(Integer, primary_key=True)
    # Identifiers
    public_id = Column(String)
    public_origin_id = Column(String)
    public_magnitude_id = Column(String)
    # Origin
    date_time = Column(DateTime)
    lat = Column(Float)
    lon = Column(Float)
    depth = Column(Float)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    # Magnitude
    magnitude = Column(Float)
    # SeismicCatalog relation
    seismic_catalog = relationship('SeismicCatalog',
                                   secondary=_catalogs_events_table,
                                   back_populates='seismic_events')
    # endregion

    # Data attributes (required for flattening)
    data_attrs = ['magnitude', 'date_time', 'x', 'y', 'z']

    def in_region(self, region):
        """
        Tests if the event is located inside **region**

        :param Cube region: Region to test (cube)
        :return: True if the event is inside the region, false otherwise

        """
        return Point(self.x, self.y, self.z).in_cube(region)

    def copy(self):
        """ Returns a new copy of itself """

        arguments = {}
        for name, column in self.__mapper__.columns.items():
            if not (column.primary_key or column.unique):
                arguments[name] = getattr(self, name)
        copy = self.__class__(self.date_time, self.magnitude,
                              Point(self.x, self.y, self.z))
        for item in arguments.items():
            setattr(copy, *item)
        return copy

    def __init__(self, date_time, magnitude, location):
        self.date_time = date_time
        self.magnitude = magnitude
        self.x = location.x
        self.y = location.y
        self.z = location.z

    def __str__(self):
        return "M%.1f @ %s" % (self.magnitude, self.date_time.ctime())

    def __repr__(self):
        return "<SeismicEvent('%s' @ '%s')>" % (self.magnitude, self.date_time)

    def __eq__(self, other):
        if isinstance(other, SeismicEvent):
            if self.public_id and other.public_id:
                return self.public_id == other.public_id
            else:
                return all(getattr(self, a) == getattr(other, a)
                           for a in self.data_attrs)
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        else:
            return not result
