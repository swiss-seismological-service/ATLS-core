# -*- encoding: utf-8 -*-
"""
History of seismic events

"""

import logging
import traceback
from datetime import datetime
from sqlalchemy import Column, event
from sqlalchemy import Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, reconstructor, Session
from ormbase import OrmBase

from signal import Signal

from ramsisdata.geometry import Point

log = logging.getLogger(__name__)


@event.listens_for(Session, 'after_flush')
def delete_catalog_orphans(session, ctx):
    """
    Seismic catalog orphan deletion

    Seismic catalogs can have different kinds of parents, so a simple
    'delete-orphan' statement on the relation doesn't work. Instead we check
    after each flush to the db if there are any orphaned catalogs and delete
    them if necessary.

    :param Session session: The current session

    """
    if any(isinstance(i, SeismicCatalog) for i in session.dirty):
        query = session.query(SeismicCatalog).\
                filter_by(project=None, forecast_input=None, skill_test=None)
        orphans = query.all()
        print('deleting orphaned catalogs: {}'.format(orphans))
        for orphan in orphans:
            session.delete(orphan)


class SeismicCatalog(OrmBase):
    """
    Provides a history of seismic events and functions to read and write them
    from/to a persistent store. The class uses Qt signals to signal changes.

    """

    # region ORM Declarations
    __tablename__ = 'seismic_catalogs'
    id = Column(Integer, primary_key=True)
    catalog_date = Column(DateTime)
    # SeismicEvent relation (we own them)
    seismic_events = relationship('SeismicEvent',
                                  order_by='SeismicEvent.date_time',
                                  back_populates='seismic_catalog',
                                  cascade='all, delete-orphan')
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

    def __init__(self):
        super(SeismicCatalog, self).__init__()
        self.history_changed = Signal()

    @reconstructor
    def init_on_load(self):
        self.history_changed = Signal()

    def import_events(self, importer):
        """
        Imports seismic events from a data source by using an EventImporter

        The EventImporter must return the following fields. All imported events
        are simply added to any existing ones. If you want to overwrite
        existing events, call :meth:`clear_events` first.

        lat: latitude [degrees]
        lon: longitude [degrees]
        depth: depth [m], positive downwards
        mag: magnitude

        :param importer: an EventImporter object
        :type importer: EventImporter

        """
        events = []
        try:
            for date, fields in importer:
                location = (float(fields['lat']),
                            float(fields['lon']),
                            float(fields['depth']))
                event = SeismicEvent(date, float(fields['mag']), location)
                events.append(event)
        except:
            log.error('Failed to import seismic events. Make sure '
                      'the data contains lat, lon, depth, and mag '
                      'fields and that the date field has the format '
                      'dd.mm.yyyyTHH:MM:SS. The original error was ' +
                      traceback.format_exc())
        else:
            self.seismic_events.extend(events)
            log.info('Imported {} seismic events.'.format(len(events)))
            self.history_changed.emit()

    def events_before(self, end_date, mc=0):
        """ Returns all events >mc before *end_date* """
        return [e for e in self.seismic_events
                if e.date_time < end_date and e.magnitude > mc]

    def clear_events(self, time_range=(None, None)):
        """
        Clear all seismic events from the database

        If time_range is given, only the events that fall into the time range
        are cleared.

        """
        time_range = (time_range[0] or datetime.min,
                      time_range[1] or datetime.max)

        to_delete = (s for s in self.seismic_events
                     if time_range[1] >= s.date_time >= time_range[0])
        count = 0
        for s in to_delete:
            self.seismic_events.remove(s)
            count += 1
        log.info('Cleared {} seismic events.'.format(count))
        self.history_changed.emit()

    def snapshot(self, t):
        """
        Create a snapshot of the catalog.

        Deep copies the catalog with all events up to time t

        :return SeismicCatalog: copy of the catalog

        """
        snapshot = SeismicCatalog()
        snapshot.catalog_date = datetime.utcnow()
        snapshot.seismic_events = [s.copy() for s in self.seismic_events
                                   if s.date_time < t]
        return snapshot

    def __len__(self):
        return len(self.seismic_events)

    def __getitem__(self, item):
        return self.seismic_events[item] if self.seismic_events else None


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
    # Magnitude
    magnitude = Column(Float)
    # SeismicCatalog relation
    seismic_catalog_id = Column(Integer, ForeignKey('seismic_catalogs.id'))
    seismic_catalog = relationship('SeismicCatalog',
                                   back_populates='seismic_events')
    # endregion

    # Data attributes (required for copying, serialization to matlab)
    copy_attrs = ['public_id', 'public_origin_id', 'public_magnitude_id']
    data_attrs = ['magnitude', 'date_time', 'lat', 'lon', 'depth']

    def in_region(self, region):
        """
        Tests if the event is located inside **region**

        :param Cube region: Region to test (cube)
        :return: True if the event is inside the region, false otherwise

        """
        return Point(self.x, self.y, self.z).in_cube(region)

    def copy(self):
        """ Return a copy of this event """
        copy = SeismicEvent(self.date_time, self.magnitude,
                            (self.lat, self.lon, self.depth))
        for attr in SeismicEvent.copy_attrs:
            setattr(copy, attr, getattr(self, attr))
        return copy

    def __init__(self, date_time, magnitude, location):
        self.date_time = date_time
        self.magnitude = magnitude
        self.lat, self.lon, self.depth = location

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
