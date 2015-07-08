# -*- encoding: utf-8 -*-
"""
All Atls settings and their default values are handled from here.
If you add new settings define their default values in the known_settings
variable. If the settings should be accessible from the settings dialog in the
GUI too, make sure you add the corresponding Qt widget to the widget_map in
settingswindow.py

Note that the module expects that the v2 API is used for QVariant (which is
set in the Atls top level object)
    
Copyright (C) 2013, ETH Zurich - Swiss Seismological Service SED

"""

from PyQt4.QtCore import QSettings
from datetime import datetime

import logging

# known settings and their default values
known_settings = {
    # General Settings (Qt automatically looks for top level keys in the general section)
    'recent_files':                 None,    # List of recently opened projects (paths)
    'project':                      None,    # Project to load on startup (overrides open_last_project)
    'open_last_project':            False,   # Open the last project when the app starts
    'enable_lab_mode':              True,    # Enable lab mode to simulate through existing data
    # Forecast Engine
    'engine/persist_results':       True,    # Store forecast results in database
    'engine/export_results':        False,   # Export results to the file system
    'engine/output_directory':      None,    # Output directory for results, if none it writes to the app directory
    'engine/fc_interval':           6.0,     # Forecasting interval [hours]
    'engine/fc_bin_size':           6.0,     # Length of each forecast bin [hours]
    'engine/rt_interval':           1.0,     # Rate computation interval [minutes]
    # Lab mode settings
    'lab_mode/infinite_speed':      True,    # Simulate through catalog as fast as possible
    'lab_mode/speed':               1000,    # Simulation speed (factor), ignored if lab_mode/infinite_speed is True
    # FIXME: fc start is project specific but also something the user might want to specify on a per run basis. find better solution.
    'lab_mode/forecast_start':      '2006-12-04 00:00:00',    # Time of the first forecast in iso format '2014-06-12 18:30:00'
    # ISHA model settings
    'ISHA/models':                  ['all'],   # List of ISHA models to load (or 'all')
}


class AppSettings:
    """
    Manages application settings.

    To access settings through this class, make sure the settings key and
    default value are registered in known_settings.

    """

    def __init__(self, settings_file=None):
        """
        Load either the user specific settings or, if a file name is
        provided, specific settings from that file.

        """
        self._settings_file = settings_file
        self._logger = logging.getLogger(__name__)
        if settings_file is None:
            self._settings = QSettings()
        else:
            self._logger.info('Loading settings from ' + settings_file)
            self._settings = QSettings(settings_file, QSettings.IniFormat)

    @property
    def settings(self):
        """
        Provides direct access to the underlying QSettings that are used to
        read/store settings values.

        """
        return self._settings

    def date_value(self, key):
        """
        Reads the string value in *key* and tries to decode it into a
        datetime object. The string value is expected to have the format
        '2014-12-24 18:00:00'

        """
        date_str = self.value(key, type=str)
        if date_str is None:
            return None
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            self._logger.error(date_str + ' could not be decoded. Ignoring.')
            return None
        else:
            return date

    def value(self, key, **kwargs):
        """
        Returns the value that is stored for key or the default value if
        no value is stored.

        If the key is not known, the function will throw an exception.

        """
        if not key in known_settings.keys():
            raise Exception(key + ' is not a known registered setting')
        default = known_settings[key]
        return self._settings.value(key, defaultValue=default, **kwargs)

    def set_value(self, key, value):
        """
        Sets the value for key

        If the key is not known, the function will throw an exception.

        """
        if not key in known_settings.keys():
            raise Exception(key + ' is not a known registered setting')
        return self._settings.setValue(key, value)

    def register_default_settings(self):
        """
        Writes the default value for each setting to the settings file

        """
        self._logger.info('Loading default settings')
        for key, value in known_settings.iteritems():
            self._settings.setValue(key, value)
        self._settings.sync()