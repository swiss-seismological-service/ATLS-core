# Copyright 2018, ETH Zurich - Swiss Seismological Service SED
"""
Data fetching facilities.
"""

import csv
import logging
from time import strptime, mktime
from datetime import datetime, timedelta

import requests

from PyQt5 import QtCore

from RAMSIS.config import FDSNWS_NOCONTENT_CODES
from RAMSIS.io.hydraulics import (HYDWSBoreholeHydraulicsDeserializer,
                                  HYDWSJSONIOError)
from RAMSIS.io.seismics import (QuakeMLCatalogDeserializer,
                                QuakeMLCatalogIOError)
from RAMSIS.io.utils import (binary_request, pymap3d_transform_geodetic2ned,
                             NoContent, RequestsError)


class CsvEventImporter:
    """
    Imports seismic events from a csv file

    CsvEventImporter assumes that the file to import contains a *date* column
    that either has relative dates (floats) or absolute dates (date string
    according to strptime()

    """

    def __init__(self, csv_file, delimiter=' ', date_field='date'):
        """
        Creates a new importer to read a csv file. EventImporter expects a
        file that is ready for reading, i.e. it needs to be opened externally

        :param csv_file: file handle
        :param delimiter: single character that delimits the columns
        :param date_field: name of the column that contains the date

        """
        self.file = csv_file
        self.delimiter = delimiter
        self.date_field = date_field
        self.base_date = datetime(1970, 1, 1)
        self.date_format = None
        self._dates_are_relative = None

    @property
    def expects_base_date(self):
        """
        Checks whether the file contains relative dates and the importer
        expects a base date to parse the file.

        Side effect: rewinds the file when called for the first time

        """

        if self._dates_are_relative is None:
            reader = csv.DictReader(self.file,
                                    delimiter=self.delimiter,
                                    skipinitialspace=True)
            first_row = next(reader)
            date = first_row[self.date_field]
            self._dates_are_relative = True
            try:
                float(date)
            except ValueError:
                self._dates_are_relative = False
            self.file.seek(0)

        return self._dates_are_relative

    def __iter__(self):
        """
        Iterator for the importer. Parses rows and returns the data in a tuple.

        The tuple contains the absolute date of the event and a dictionary
        with all fields that were read.

        """
        reader = csv.DictReader(self.file,
                                delimiter=self.delimiter,
                                skipinitialspace=True)

        for row in reader:
            if self._dates_are_relative:
                days = float(row[self.date_field])
                date = self.base_date + timedelta(days=days)
            else:
                time_struct = strptime(row[self.date_field], self.date_format)
                date = datetime.fromtimestamp(mktime(time_struct))

            yield (date, row)


class HYDWSDataSource(QtCore.QThread):
    """
    QThread fetching and deserializing data from *HYDWS*.
    """
    DESERIALZER = HYDWSBoreholeHydraulicsDeserializer

    data_received = QtCore.pyqtSignal(object)

    def __init__(self, url, timeout=None, proj=None):
        super().__init__()
        self.url = url

        self._args = {}
        self.enabled = False
        self.logger = logging.getLogger(__name__)

        self._deserializer = self.DESERIALZER(
            proj=proj,
            transform_callback=pymap3d_transform_geodetic2ned)

    def fetch(self, **kwargs):
        """
        Fetch data by means of a background-thread

        :param kwargs: args dict forwarded to the HYDWS
        """
        self._args = kwargs
        if self.enabled:
            self.start()

    def run(self):
        bh = None

        self.logger.debug(
            f"Request seismic catalog from fdsnws-event (url={self._url}, "
            f"params={self._params}).")
        try:
            with binary_request(
                requests.get, self.url, self._args, self._timeout,
                    nocontent_codes=FDSNWS_NOCONTENT_CODES) as ifd:
                bh = self._deserializer.load(ifd)

        except NoContent:
            self.logger.info('No data received.')
        except RequestsError as err:
            self.logger.error(f"Error while fetching data ({err}).")
        except HYDWSJSONIOError as err:
            self.logger.error(f"Error while deserializing data ({err}).")
        else:
            self.logger.info(
                f"Received borehole data with {len(bh)} sections.")

        self.data_received.emit(bh)


class FDSNWSDataSource(QtCore.QThread):
    """
    Fetches seismic event data from a web service in the background.
    """

    DESERIALZER = QuakeMLCatalogDeserializer

    data_received = QtCore.pyqtSignal(object)

    def __init__(self, url, timeout=None, proj=None):
        super().__init__()
        self.url = url
        self._timeout = None

        self._args = {}
        self.enabled = False
        self.logger = logging.getLogger(__name__)

        self._deserializer = self.DESERIALZER(
            proj=proj,
            transform_callback=pymap3d_transform_geodetic2ned)

    def fetch(self, **kwargs):
        """
        Fetch data by means of a background-thread

        :param kwargs: args dict forwarded to fdsnws-event
        """
        self._args = kwargs
        if self.enabled:
            self.start()

    def run(self):
        cat = None

        self.logger.debug(
            f"Request seismic catalog from fdsnws-event (url={self._url}, "
            f"params={self._params}).")
        try:
            with binary_request(
                requests.get, self.url, self._args, self._timeout,
                    nocontent_codes=FDSNWS_NOCONTENT_CODES) as ifd:
                cat = self._deserializer.load(ifd)

        except NoContent:
            self.logger.info('No data received.')
        except RequestsError as err:
            self.logger.error(f"Error while fetching data ({err}).")
        except QuakeMLCatalogIOError as err:
            self.logger.error(f"Error while deserializing data ({err}).")
        else:
            self.logger.info(
                f"Received catalog with {len(cat)} events.")

        self.data_received.emit(cat)
