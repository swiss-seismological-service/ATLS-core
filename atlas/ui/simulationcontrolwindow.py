# -*- encoding: utf-8 -*-
"""
Controller class for the simulation control window
    
Copyright (C) 2013, ETH Zurich - Swiss Seismological Service SED

"""

import logging
from PyQt4 import QtGui
from atlascore import CoreState
from views.ui_simulationcontrolwindow import Ui_SimulationControlWindow

class SimulationControlWindow(QtGui.QDialog):

    def __init__(self, atlas_core, **kwargs):
        QtGui.QDialog.__init__(self, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.atlas_core = atlas_core

        # Setup the user interface
        self.ui = Ui_SimulationControlWindow()
        self.ui.setupUi(self)

        # Connect buttons
        self.ui.startButton.pressed.connect(self.action_start_forecast)
        self.ui.pauseButton.pressed.connect(self.action_pause_forecast)
        self.ui.stopButton.pressed.connect(self.action_stop_forecast)
        # ... other controls
        self.ui.infiniteSpeedCheckBox.checkStateSet.\
            connect(self.action_infinite_speed_changed)
        self.ui.speedBox.valueChanged.connect(self.action_sim_speed_changed)
        # Hook up essential signals from the core and the forecast engine
        self.atlas_core.state_changed.connect(self.on_core_state_change)

    # Button Action Signals

    def action_start_forecast(self):
        speed = self.ui.speedBox.value()
        if self.ui.infiniteSpeedCheckBox.checkState():
            self.atlas_core.start_simulation(infinite_speed=True)
        else:
            self.atlas_core.simulator.speed = speed
            self.atlas_core.start_simulation(infinite_speed=False)

    def action_pause_forecast(self):
        self.atlas_core.action_pause_simulation()

    def action_stop_forecast(self):
        self.atlas_core.action_stop_simulation()

    def action_sim_speed_changed(self):
        speed = self.ui.speedBox.value()
        self.atlas_core.simulator.speed = speed

    def action_infinite_speed_changed(self):
        if self.ui.infiniteSpeedCheckBox.checkState():
            self.ui.speedBox.setEnabled(False)
        else:
            self.ui.speedBox.setEnabled(True)

    # Signals from the core

    def on_core_state_change(self):
        self.update_controls()

    # UI Updates

    def update_controls(self):
        """ Enables or disables controls depending on the core state """
        state = self.atlas_core.state
        if state == CoreState.SIMULATING:
            self.ui.infiniteSpeedCheckBox.setEnabled(False)
            self.ui.startButton.setEnabled(False)
            self.ui.pauseButton.setEnabled(True)
            self.ui.stopButton.setEnabled(True)
        elif state == CoreState.PAUSED:
            self.ui.infiniteSpeedCheckBox.setEnabled(False)
            self.ui.startButton.setEnabled(True)
            self.ui.pauseButton.setEnabled(False)
            self.ui.stopButton.setEnabled(True)
        elif state == CoreState.FORECASTING:
            self.ui.infiniteSpeedCheckBox.setEnabled(False)
            self.ui.startButton.setEnabled(False)
            self.ui.pauseButton.setEnabled(True)
            self.ui.stopButton.setEnabled(True)
        else:
            # IDLE
            self.ui.infiniteSpeedCheckBox.setEnabled(True)
            self.ui.startButton.setEnabled(True)
            self.ui.pauseButton.setEnabled(False)
            self.ui.stopButton.setEnabled(False)
