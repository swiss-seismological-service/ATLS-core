# -*- encoding: utf-8 -*-
# Copyright (C) 2013, ETH Zurich - Swiss Seismological Service SED

"""
Provides a class to manage Ramsis project data

"""

from datetime import datetime

from PyQt4 import QtCore
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, reconstructor
from ormbase import OrmBase, DeclarativeQObjectMeta

from seismics import SeismicCatalog
from hydraulics import InjectionHistory
from forecast import ForecastSet
from injectionwell import InjectionWell


class Project(QtCore.QObject, OrmBase):
    """
    Manages persistent and non-persistent ramsis project data such as the
    seismic and hydraulic history, and project state information.

    .. pyqt4:signal:project_time_changed: emitted when the project time changes

    :ivar seismic_catalog: The seismic history of the project
    :ivar injection_history: The hydraulic history of the project

    """
    __metaclass__ = DeclarativeQObjectMeta

    # region ORM Declarations
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    args = {'uselist': False,  # we use one to one relationships for now
            'back_populates': 'project',
            'cascade': 'all, delete-orphan'}
    injection_well = relationship('InjectionWell', **args)
    injection_history = relationship('InjectionHistory', **args)
    forecast_set = relationship('ForecastSet', **args)
    seismic_catalog = relationship('SeismicCatalog',
                                   **dict(args, cascade='all'))
    # endregion

    # Signals
    will_close = QtCore.pyqtSignal(object)
    project_time_changed = QtCore.pyqtSignal(datetime)

    def __init__(self, title=''):
        """ Create a new project and persist to database """
        super(Project, self).__init__()
        self.title = title
        # FIXME: hardcoded for testing purposes
        # These are the basel well tip coordinates (in CH-1903)
        self.injection_well = InjectionWell(4740.3, 270645.0, 611631.0)
        self.injection_history = InjectionHistory()
        self.forecast_set = ForecastSet()
        self.seismic_catalog = SeismicCatalog()
        self._project_time = None
        self.init_on_load()

    @reconstructor
    def init_on_load(self):
        # Set the project time to the time of the first event
        event = self.earliest_event()
        self._project_time = event.date_time if event else datetime.now()

    def close(self):
        """
        Closes the project file. Before closing, the *will_close* signal is
        emitted. After closing, the project is not usable anymore and will have
        to be reinstatiated if it is needed again.

        """
        self.will_close.emit(self)

    @property
    def project_time(self):
        return self._project_time

    # Event information

    def event_time_range(self):
        """
        Returns the time range of all events in the project as a (start_time,
        end_time) tuple.

        """
        earliest = self.earliest_event()
        latest = self.latest_event()
        start = earliest.date_time if earliest else None
        end = latest.date_time if latest else None
        return start, end

    def earliest_event(self):
        """
        Returns the earliest event in the project, either seismic or hydraulic.

        """
        try:
            es = self.seismic_catalog[0]
            eh = self.injection_history[0]
        except IndexError:
            return None
        if es is None and eh is None:
            return None
        elif es is None:
            return eh
        elif eh is None:
            return es
        else:
            return eh if eh.date_time < es.date_time else es

    def latest_event(self):
        """
        Returns the latest event in the project, either seismic or hydraulic.

        """
        try:
            es = self.seismic_catalog[-1]
            eh = self.injection_history[-1]
        except IndexError:
            return None
        if es is None and eh is None:
            return None
        elif es is None:
            return eh
        elif eh is None:
            return es
        else:
            return eh if eh.date_time > es.date_time else es

    # Project time

    def update_project_time(self, t):
        self._project_time = t
        self.project_time_changed.emit(t)
