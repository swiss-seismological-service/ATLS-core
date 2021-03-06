# -*- encoding: utf-8 -*-
"""
Controller class for the main window

Takes care of setting up the main GUI, handling any menu actions and updating
top level controls as necessary.
We delegate the presentation of content to a content presenter so that this
class does not become too big.

Copyright (C) 2017, ETH Zurich - Swiss Seismological Service SED

"""

import logging
import os

from PyQt5 import uic
from PyQt5.QtWidgets import QSizePolicy, QWidget, QStatusBar, QLabel, \
    QMessageBox, QProgressBar, QMainWindow, QAction, QFileDialog, QTableView

from RAMSIS.core.simulator import SimulatorState
from RAMSIS.core.datasources import CsvEventImporter
import RAMSIS.ui.ramsisuihelpers as helpers

from RAMSIS.ui.settingswindow import (
    ApplicationSettingsWindow, ProjectSettingsWindow)
from RAMSIS.ui.simulationwindow import SimulationWindow
from RAMSIS.ui.reservoirwindow import ReservoirWindow
from RAMSIS.ui.ramsisuihelpers import utc_to_local

from .presenter import ContentPresenter
from .viewmodels.seismicdatamodel import SeismicDataModel
from ramsis.datamodel.forecast import Scenario


ui_path = os.path.dirname(__file__)
MAIN_WINDOW_PATH = os.path.join(ui_path, '..', 'views', 'mainwindow.ui')
Ui_MainWindow = uic.loadUiType(
    MAIN_WINDOW_PATH,
    import_from='RAMSIS.ui.views', from_imports=True)[0]


class StatusBar(QStatusBar):

    def __init__(self):
        super(StatusBar, self).__init__()
        self.projectWidget = QLabel('No project loaded')
        self.timeWidget = QLabel('Project Time: N/A')
        self.progressBar = QProgressBar()
        self.progressBar.setMaximumHeight(15)
        self.progressBar.setMaximumWidth(150)
        self.activityWidget = QLabel('Idle')
        self.current_activity_id = None
        self.addWidget(self.projectWidget)
        self.addWidget(QLabel(' '*10))
        self.addWidget(self.timeWidget)
        self.addPermanentWidget(self.activityWidget)
        self.addPermanentWidget(self.progressBar)
        self.progressBar.setHidden(True)

    def set_project(self, project):
        txt = project.title if project else 'No project loaded'
        self.projectWidget.setText(txt)
        self.set_project_time(project.project_time if project else None)

    def set_project_time(self, t):
        txt = utc_to_local(t).strftime('%d.%m.%Y %H:%M:%S') if t else 'N/A'
        self.timeWidget.setText('Project Time: {}'.format(txt))

    def show_activity(self, message, id='default'):
        self.current_activity_id = id
        self.progressBar.setRange(0, 0)
        self.progressBar.setHidden(False)
        self.activityWidget.setText(message)

    def dismiss_activity(self, id='default'):
        if self.current_activity_id == id:
            self.progressBar.setHidden(True)
            self.activityWidget.setText('Idle')
            self.current_activity_id = None


class MainWindow(QMainWindow):

    def __init__(self, ramsis, *args, **kwargs):
        print(MainWindow.__mro__)
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

        # Other windows which we lazy-load
        self.application_settings_window = None
        self.project_settings_window = None
        self.reservoir_window = None
        self.simulation_window = None
        self.timeline_window = None
        self.table_view = None

        # References
        self.ramsis_core = ramsis.ramsis_core
        self.application_settings = ramsis.app_settings

        # Setup the user interface
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # ...additional setup
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        spacer.setVisible(True)
        self.ui.mainToolBar.insertWidget(self.ui.actionShow_3D, spacer)
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

        # Delegate content presentation
        self.content_presenter = ContentPresenter(self.ramsis_core, self.ui)

        # Hook up the menu
        # ...File
        self.ui.actionNew_Project.triggered.connect(self.action_new_project)
        self.ui.actionOpen_Project.triggered.connect(self.action_open_project)
        self.ui.actionFetch_from_fdsnws.triggered.connect(
            self.action_fetch_seismic_data)
        self.ui.actionFetch_from_hydws.triggered.connect(
            self.action_fetch_hydraulic_data)
        self.ui.actionImport_Seismic_Data.triggered.connect(
            self.action_import_seismic_data)
        self.ui.actionImport_Hydraulic_Data.triggered.connect(
            self.action_import_hydraulic_data)
        self.ui.actionView_Data.triggered.\
            connect(self.action_view_seismic_data)
        self.ui.actionApplication_Settings.triggered.connect(
            self.action_show_application_settings)
        self.ui.actionProject_Settings.triggered.connect(
            self.action_show_project_settings)
        self.ui.actionDelete_Results.triggered.connect(
            self.action_delete_results)
        # ...Forecast planning
        self.ui.addScenarioButton.clicked.connect(
            self.on_add_scenario_clicked)
        self.ui.removeScenarioButton.clicked.connect(
            self.on_remove_scenario_clicked)
        self.ui.planNextButton.clicked.connect(
            self.on_plan_next_forecast_clicked
        )
        # ...Simulation
        self.ui.actionStart_Simulation.triggered.\
            connect(self.action_start_simulation)
        self.ui.actionPause_Simulation.triggered.\
            connect(self.action_pause_simulation)
        self.ui.actionStop_Simulation.triggered.\
            connect(self.action_stop_simulation)
        # ...Window
        self.ui.actionShow_3D.triggered.connect(self.action_show_3d)
        self.ui.actionSimulation.triggered.\
            connect(self.action_show_sim_controls)

        # Connect essential signals
        # ... from the core
        ramsis.app_launched.connect(self.on_app_launch)
        self.ramsis_core.project_loaded.connect(self.on_project_load)
        self.ramsis_core.simulator.state_changed.\
            connect(self.on_sim_state_change)

    # Menu Actions

    def action_open_project(self):
        home = os.path.expanduser("~")
        path = QFileDialog.getOpenFileName(None, 'Open Project', home,
                                           'Ramsis Project Files (*.db)')[0]
        if path == '':
            return
        self._open_project_at_path(path)

    def _open_project_at_path(self, path):
        if path is None:
            return
        if self.ramsis_core.project is not None:
            self.ramsis_core.close_project()
        self.ramsis_core.open_project(str(path))
        # Update the list of recent files
        recent_files = self.application_settings.value('recent_files')
        if recent_files is None:
            recent_files = []
        if path in recent_files:
            recent_files.insert(0,
                                recent_files.pop(recent_files.index(path)))
        else:
            recent_files.insert(0, path)
        del recent_files[4:]
        self.application_settings.set_value('recent_files', recent_files)
        self._refresh_recent_files_menu()

    def _refresh_recent_files_menu(self):
        files = self.application_settings.value('recent_files')
        self.ui.menuOpen_Recent.clear()
        if files is None:
            return
        for path in files:
            path = str(path)
            file_name = os.path.basename(path)
            file_action = QAction(file_name, self)
            file_action.setData(path)
            file_action.triggered.connect(self.action_open_recent)
            self.ui.menuOpen_Recent.addAction(file_action)

    def action_open_recent(self):
        sender_action = self.sender()
        path = str(sender_action.data())
        self._open_project_at_path(path)

    def action_new_project(self):
        home = os.path.expanduser("~")
        path = QFileDialog. \
            getSaveFileName(None, 'New Project', home,
                            'Ramsis Project Files (*.db)')
        if not path.endswith('.db'):
            path += '.db'
        self.ramsis_core.create_project(path)
        self._open_project_at_path(path)

    def action_fetch_seismic_data(self):
        self.status_bar.show_activity('Fetching seismic data...',
                                      id='fdsn_fetch')
        self.ramsis_core.fetch_seismic_events()

    def action_import_seismic_data(self):
        home = os.path.expanduser("~")
        path = QFileDialog.getOpenFileName(None,
                                           'Open seismic data file',
                                           home)
        if path == '':
            return
        history = self.ramsis_core.project.seismic_catalog
        if path:
            self._import_file_to_history(path, history)

    def action_fetch_hydraulic_data(self):
        self.status_bar.show_activity('Fetching hydraulic data...',
                                      id='hydws_fetch')
        self.ramsis_core.fetch_hydraulic_events()

    def action_import_hydraulic_data(self):
        home = os.path.expanduser("~")
        path = QFileDialog.getOpenFileName(None,
                                           'Open hydraulic data file',
                                           home)
        if path == '':
            return
        history = self.ramsis_core.project.injection_history
        if path:
            self._import_file_to_history(path, history, delimiter='\t')

    def action_delete_results(self):
        reply = QMessageBox.question(
            self,
            "Delete results",
            "Are you sure you want to delete all forecast results? This "
            "cannot be undone!",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.ramsis_core.delete_results()

    def _import_file_to_history(self, path, history, delimiter=' '):
        """
        Import happens on the view level (instead of inside Project) because
        the process is interactive. The function checks if the file contains
        relative dates. If yes, the user is asked to provide a base date.

        :param str path: Path to csv file
        :param SeismicCatalog | HydraulicHistory: Target history
        :param str delimiter: Delimiter used to delimit records

        """
        with open(path, 'rb') as csv_file:
            importer = CsvEventImporter(csv_file, delimiter=delimiter)
            if importer.expects_base_date:
                date, accepted = helpers.DateDialog.get_date_time()
                if not accepted:
                    return
                importer.base_date = date
            else:
                importer.date_format = '%Y-%m-%dT%H:%M:%S'
            history.clear_events()
            history.import_events(importer)
            self.ramsis_core.project.save()

    def action_show_sim_controls(self):
        if self.simulation_window is None:
            self.simulation_window = \
                SimulationWindow(ramsis_core=self.ramsis_core, parent=self)
        self.simulation_window.show()

    def action_show_3d(self):
        self.reservoir_window = ReservoirWindow(self.ramsis_core)
        self.reservoir_window.show()
        self.reservoir_window.draw_catalog()

    def action_show_application_settings(self):
        if self.application_settings_window is None:
            self.application_settings_window = \
                ApplicationSettingsWindow(
                    settings=self.application_settings)
        self.application_settings_window.show()

    def action_show_project_settings(self):
        if self.project_settings_window is None:
            self.project_settings_window = \
                ProjectSettingsWindow(project=self.ramsis_core.project)
        self.project_settings_window.show()

    def action_view_seismic_data(self):
        if self.table_view is None:
            self.table_view = QTableView()
            model = SeismicDataModel(self.ramsis_core.project.seismic_catalog)
            self.table_view.setModel(model)
            self.table_view.show()

    # ... Simulation

    def action_start_simulation(self):
        # speed = self.ui.speedBox.value()
        # self.ramsis_core.simulator.speed = speed
        self.ramsis_core.start()

    def action_pause_simulation(self):
        self.ramsis_core.pause()

    def action_stop_simulation(self):
        self.ramsis_core.stop()

    # Menu Enabled State Updates

    def update_controls(self):
        enable_with_project = [
            'menuProject',
            'actionShow_3D', 'actionSimulation',
            'actionScenario', 'planNextButton', 'addScenarioButton',
            'removeScenarioButton',
        ]
        enable = True if self.ramsis_core.project is not None else False
        for ui_element in enable_with_project:
            getattr(self.ui, ui_element).setEnabled(enable)

        project = self.ramsis_core.project
        if not project:
            self.ui.actionStart_Simulation.setEnabled(False)
            self.ui.actionPause_Simulation.setEnabled(False)
            self.ui.actionStop_Simulation.setEnabled(False)
            return
        sim_state = self.ramsis_core.simulator.state
        if sim_state == SimulatorState.RUNNING:
            self.ui.actionStart_Simulation.setEnabled(False)
            self.ui.actionPause_Simulation.setEnabled(True)
            self.ui.actionStop_Simulation.setEnabled(True)
        elif sim_state == SimulatorState.PAUSED:
            self.ui.actionStart_Simulation.setEnabled(True)
            self.ui.actionPause_Simulation.setEnabled(False)
            self.ui.actionStop_Simulation.setEnabled(True)
        else:
            # STOPPED
            self.ui.actionStart_Simulation.setEnabled(True)
            self.ui.actionPause_Simulation.setEnabled(False)
            self.ui.actionStop_Simulation.setEnabled(False)

        en = (project.settings['fdsnws_enable'] is True and
              project.settings['fdsnws_url'] is not None)
        self.ui.actionFetch_from_fdsnws.setEnabled(en)

        en = (project.settings['hydws_enable'] is True and
              project.settings['hydws_url'] is not None)
        self.ui.actionFetch_from_hydws.setEnabled(en)

    # Status Updates

    def update_status_msg(self):
        """
        Updates the status message in the status bar.

        """
        if self.ramsis_core.simulator.state == SimulatorState.RUNNING:
            state_msg = 'Simulating'
        elif self.ramsis_core.simulator.state == SimulatorState.PAUSED:
            state_msg = 'Simulating (paused)'
        else:
            self.status_bar.dismiss_activity('simulator_state')
            return

        self.status_bar.show_activity(state_msg, 'simulator_state')

    # UI signals

    def on_add_scenario_clicked(self):
        fc_selection = self.ui.forecastTreeView.selectionModel()
        idx = fc_selection.currentIndex()
        if idx.parent().isValid():
            forecast_idx = idx.parent().row()
        else:
            forecast_idx = idx.row()
        try:
            forecast_set = self.content_presenter.fc_tree_model.forecast_set
            forecast = forecast_set.forecasts[forecast_idx]
            scenario = Scenario()
            scenario.name = 'new scenario'
            forecast.add_scenario(scenario)
            self.ramsis_core.project.store.commit()
        except IndexError as e:
            raise e

    def on_remove_scenario_clicked(self):
        fc_selection = self.ui.forecastTreeView.selectionModel()
        idx = fc_selection.currentIndex()
        if idx.parent().isValid():
            forecast_idx = idx.parent().row()
            scenario_idx = idx.row()
        else:
            forecast_idx = idx.row()
            scenario_idx = 0
        try:
            forecast_set = self.content_presenter.fc_tree_model.forecast_set
            forecast = forecast_set.forecasts[forecast_idx]
            scenario = forecast.input.scenarios[scenario_idx]
            forecast.remove_scenario(scenario)
            self.ramsis_core.project.store.commit()
        except IndexError:
            pass

    def on_plan_next_forecast_clicked(self):
        self.ramsis_core.create_next_future_forecast()

    # Handlers for signals from the core

    def on_app_launch(self):
        self._refresh_recent_files_menu()
        self.update_controls()

    def on_project_will_close(self, _):
        self.status_bar.set_project(None)
        self.update_controls()

    def on_project_time_change(self, t):
        self.status_bar.set_project_time(t)

    def on_project_load(self, project):
        """
        :param project: RAMSIS project
        :type project: Project

        """
        self.content_presenter.present_current_project()
        self.status_bar.set_project(project)
        project.settings.settings_changed.connect(
            self.on_project_settings_changed)
        project.seismic_catalog.history_changed.connect(
            self.on_catalog_changed)
        project.project_time_changed.connect(self.on_project_time_change)
        self.update_controls()

    def on_catalog_changed(self, _):
        self.status_bar.dismiss_activity('fdsn_fetch')

    def on_sim_state_change(self, _):
        self.update_controls()
        self.update_status_msg()

    def on_project_settings_changed(self, settings):
        self.update_controls()
        self.status_bar.set_project(self.ramsis_core.project)
