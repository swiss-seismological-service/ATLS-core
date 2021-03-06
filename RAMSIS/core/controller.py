# -*- encoding: utf-8 -*-
"""
RAMSIS Core Controller.

This module defines a single class `Controller` which acts as the
central coordinator for all core components.

"""

import logging
import os
from PyQt5 import QtCore
from collections import namedtuple
from datetime import timedelta

from RAMSIS.core.datasources import FDSNWSDataSource, HYDWSDataSource
from RAMSIS.core.engine.engine import Engine
from RAMSIS.core.simulator import Simulator, SimulatorState
from RAMSIS.core.taskmanager import TaskManager
from ramsis.datamodel.forecast import Forecast, ForecastInput, Scenario
from ramsis.datamodel.hydraulics import InjectionPlan, InjectionSample
from ramsis.datamodel.ormbase import OrmBase
from ramsis.datamodel.project import Project
from ramsis.datamodel.store import Store

# from core.tools.tools import Profiler

TaskRunInfo = namedtuple('TaskRunInfo', 't_project')
"""
Used internally to pass information to repeating tasks
t_project is the project time at which the task is launched

"""


class Controller(QtCore.QObject):
    """
    RT-RAMSIS Core Controller Class

    A singleton instance of `Controller` is created when the program
    launches. The `Controller` is responsible for setting up and connecting
    all other core components, so it effectively bootstraps the application
    logic.

    At run time, the `Controller` acts as the central entry point for
    the user interface.

    :ivar Project project: Currently loaded project
    :param AppSettings settings: reference to the application settings

    """

    project_loaded = QtCore.pyqtSignal(object)

    def __init__(self, settings):
        super(Controller, self).__init__()
        self._settings = settings
        self.project = None
        self.engine = Engine(self)
        self.fdsnws_previous_end_time = None
        self.hydws_previous_end_time = None
        self.seismics_data_source = None
        self.hydraulics_data_source = None

        # Initialize simulator
        self.simulator = Simulator(self._simulation_handler)

        # Task Manager
        self.task_manager = TaskManager(core=self)

        # Time, state and other internals
        self._logger = logging.getLogger(__name__)
        # self._logger.setLevel(logging.DEBUG)

    # Project handling

    def open_project(self, path):
        """
        Open RAMSIS project file located at path

        :param str path: path to the ramsis project file

        """
        if not os.path.exists(path):
            self._logger.error('Could not find project: ' + path)
            return
        # We add an additional / in front of the url. So now we have 3 slashes
        # in total, because host and db-name section are both empty for sqlite
        store_path = 'sqlite:///' + path
        self._logger.info('Loading project at ' + path +
                          ' - This might take a while...')
        store = Store(store_path, OrmBase)
        self.project = store.session.query(Project).first()
        self.project.store = store
        self.project.settings.settings_changed.connect(
            self._on_project_settings_changed
        )
        self.engine.observe_project(self.project)
        self.project_loaded.emit(self.project)
        self._update_data_sources()
        self._logger.info('... done loading project')

    def create_project(self, path):
        """
        Create a new project at path and load it.

        If a project exists at path, it will be replaced.

        """
        if self.project:
            self.close_project()
        if os.path.exists(path):
            os.remove(path)
        store_path = 'sqlite:///' + path
        self._logger.info('Creating project at ' + path)
        store = Store(store_path, OrmBase)
        project = Project(store=store, title='New Project')
        project.save()

    def close_project(self):
        """
        Close the current project.

        """
        self.project.close()
        self.project = None

    # Other user actions

    def fetch_seismic_events(self):
        """
        Reload seismic catalog by fetching all events from the
        seismic data source.

        """
        self._logger.info('Re-fetching seismic data from data source')
        self.seismics_data_source.fetch()

    def fetch_hydraulic_events(self):
        """
        Reload hydraulic history by fetching all events from the
        hydraulic data source.

        """
        self._logger.info('Re-fetching hydraulic data from data source')
        self.hydraulics_data_source.fetch()

    def delete_results(self):
        project = self.project
        self._logger.info('Deleting all results and input catalogs')
        for forecast in project.forecast_set.forecasts:
            # As long as we have expire_on_commit=False we need to make sure
            # we have no dangling relations in the session after a delete
            # manually.
            for result in forecast.results:
                result.scenario = None
            forecast.results = []
            forecast.input.input_catalog = None
        project.save()

    # Running

    def start(self, time_range=None, speed=1):
        """
        Start the core

        This essentially enables the task manager and with it any scheduled
        operations. If a time_range is given, the simulator will be started
        to simulate the passing of time through the time range at the speed
        given in the speed paramenter.

        :param time_range: datetime tuple indicating simulation start / end
        :param speed: simulation speed, -1 for as fast as possible

        """
        if time_range:
            self.start_simulation(time_range, speed)
        else:
            self._logger.info('RAMSIS only works in sim mode at the moment')

    def pause(self):
        if self.simulator.state == SimulatorState.RUNNING:
            self.pause_simulation()

    def stop(self):
        if self.simulator.state == SimulatorState.RUNNING:
            self.stop_simulation()

    # Simulation

    def start_simulation(self, time_range, speed):
        """
        Starts the simulation.

        The simulation replays the events from the seismic and hydraulic
        histories at the simulation speed that is currently configured and
        triggers forecasts and other computations at the appropriate times.
        See :doc:`core` documentation for further information on how simulation
        works.

        If the simulation was previously paused by `pause_simulation` the
        simulation will simply continue. Otherwise, the simulator will be
        reset to the start of its :meth:`configured
        <core.simulator.Simulator.configure>` time range and begin from there.

        """
        # self._profiler = Profiler()
        # self._profiler.start()
        if self.project is None:
            return
        self._logger.info('Starting simulation')
        if self.simulator.state == SimulatorState.STOPPED:
            self._init_simulation(time_range, speed)
        # Start simulator
        self.simulator.start()

    def _init_simulation(self, time_range, speed):
        """
        (Re)initialize simulator and scheduler for a new simulation

        """
        # self._logger.info(
        #     'Deleting any forecasting results from previous runs')
        # self.project.seismic_catalog.clear()
        inf_speed = True if speed == -1 else False
        if inf_speed:
            self._logger.info('Simulating at maximum speed')
            dt_h = self.project.setting['forecast_interval']
            dt = timedelta(hours=dt_h)
            step_signal = self.engine.forecast_complete
            self.simulator.configure(time_range, step_on=step_signal, dt=dt)
        else:
            self._logger.info('Simulating at {:.0f}x'.format(speed))
            self.simulator.configure(time_range, speed=speed)
        self.task_manager.reset(time_range[0])

    def pause_simulation(self):
        """ Pauses the simulation. """
        self._logger.info('Pausing simulation')
        self.simulator.pause()

    def stop_simulation(self):
        """
        Stops the simulation.

        All seismic and hydraulic events are cleared from the database.

        """
        self._logger.info('Stopping simulation')
        self.simulator.stop()

    # Simulation handling

    def _simulation_handler(self, simulation_time):
        """ Invoked by the simulation whenever the project time changes """
        self.project.update_project_time(simulation_time)

    def create_next_future_forecast(self):
        """ Adds the next regular forecast to the list of future forecasts """
        p = self.project
        dt = timedelta(hours=p.settings['forecast_interval'])
        if len(p.forecast_set.forecasts) > 0:
            t_last = p.forecast_set.forecasts[-1].forecast_time
        else:
            t_last = self.project.settings['forecast_start'] - dt
        forecast = self.create_forecast(t_last + dt)
        p.forecast_set.add_forecast(forecast)
        p.store.commit()

    def create_forecast(self, forecast_time):
        """ Returns a new Forecast instance """

        # rows
        forecast = Forecast()
        forecast_input = ForecastInput()
        scenario = Scenario()
        scenario.name = 'Default Scenario'
        model_settings = self.project.settings['forecast_models'].items()
        scenario.config = {
            'run_is_forecast': True,
            'run_hazard': True,
            'run_risk': True,
            'disabled_models': [model_id for model_id, conf in model_settings
                                if not conf['enabled']]
        }
        injection_plan = InjectionPlan()
        injection_sample = InjectionSample(None, None, None, None, None)

        # relations
        forecast.input = forecast_input
        forecast_input.scenarios = [scenario]
        scenario.injection_plan = injection_plan
        injection_plan.samples = [injection_sample]

        # forecast attributes
        forecast.forecast_time = forecast_time
        forecast.forecast_interval = self.project.settings['forecast_length']
        forecast.mc = 0.9
        forecast.m_min = 0
        forecast.m_max = 6

        # injection_sample attributes
        injection_sample.date_time = forecast_time

        return forecast

    def _on_project_settings_changed(self, _):
        self._update_data_sources()

    def _update_data_sources(self):
        # Seismic
        new_url = self.project.settings['fdsnws_url']
        en = self.project.settings['fdsnws_enable']
        if new_url is None:
            self.seismics_data_source = None
        elif self.seismics_data_source:
            if self.seismics_data_source.url != new_url:
                self.seismics_data_source.url = new_url
                self._logger.info('Seismic data source changed to {}'
                                 .format(new_url))
            if self.seismics_data_source.enabled != en:
                self.seismics_data_source.enabled = en
                self._logger.info('Seismic data source {}'
                                  .format('enabled' if en else 'disabled'))
        else:
            self.seismics_data_source = FDSNWSDataSource(new_url)
            self.seismics_data_source.enabled = en
            self.seismics_data_source.data_received.connect(
                self._on_seismic_data_received)
        # Hydraulic
        new_url = self.project.settings['hydws_url']
        en = self.project.settings['hydws_enable']
        if new_url is None:
            self.hydraulics_data_source = None
        elif self.hydraulics_data_source:
            if self.hydraulics_data_source.url != new_url:
                self.hydraulics_data_source.url = new_url
                self._logger.info('Hydraulic data source changed to {}'
                                  .format(new_url))
            if self.hydraulics_data_source.enabled != en:
                self.hydraulics_data_source.enabled = en
                self._logger.info('Hydraulic data source {}'
                                  .format('enabled' if en else 'disabled'))
        else:
            self.hydraulics_data_source = HYDWSDataSource(new_url)
            self.hydraulics_data_source.enabled = en
            self.hydraulics_data_source.data_received.connect(
                self._on_hydraulic_data_received)

    def _on_seismic_data_received(self, result):
        if result is not None:
            tr = result['time_range']
            importer = result['importer']
            self.project.seismic_catalog.clear_events(tr)
            self.project.seismic_catalog.import_events(importer)
            self.project.store.commit()

    def _on_hydraulic_data_received(self, result):
        if result is not None:
            tr = result['time_range']
            importer = result['importer']
            self.project.injection_history.clear_events(tr)
            self.project.injection_history.import_events(importer)
            self.project.store.commit()
