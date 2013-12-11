# -*- encoding: utf-8 -*-
"""
Additions for PyQtGraph

Atlas specific classes used in various places of the user interface
    
"""

import pyqtgraph as pg
from datetime import datetime, timedelta


class DisplayRange(object):
    DAY = 24*3600
    WEEK = 7*24*3600
    MONTH = 30*7*24*3600
    DEFAULT = WEEK


class DateAxis(pg.AxisItem):
    """
    An AxisItem that displays dates

    The display format is adjusted automatically depending on the date range
    given in values.

    :param values: time values (seconds in epoch)

    """
    def tickStrings(self, values, scale, spacing):
        # FIXME: Implement this properly some time
        epoch = datetime(1970, 1, 1)
        dates = [epoch + timedelta(seconds=v) for v in values]
        strns = []
        rng = max(values) - min(values)
        #if rng < 120:
        #    return pg.AxisItem.tickStrings(self, values, scale, spacing)
        if rng < 3600*24:
            string = '%H:%M:%S'
        elif rng < 3600*24*30:
            string = '%d'
        elif rng < 3600*24*30*24:
            string = '%b'
        else:
            string = '%Y'
        for x in dates:
            try:
                strns.append(x.strftime(string))
            except ValueError:  # Windows can't handle dates before 1970
                strns.append('')

        return strns


class TimePlotWidget(pg.PlotWidget):
    """ A plot widget where the x-Axis is a DateAxis """

    def __init__(self, parent=None, **kargs):
        axis = DateAxis(orientation='bottom')
        super(TimePlotWidget, self).__init__(parent, axisItems={'bottom': axis},
                                             **kargs)

        self.setMouseEnabled(y=False)
        self._range = DisplayRange.DEFAULT

        # Current time indicator (vertical line)
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen='g')
        self.addItem(self.v_line)

    @property
    def marker_pos(self):
        return self.v_line.value()

    @marker_pos.setter
    def marker_pos(self, t):
        self.v_line.setValue(t)

    @property
    def display_range(self):
        return self._range

    def advance_time(self, dt, translate=False):
        """
        Advances the plot marker by dt and translates the view range if
        necessary.

        """
        self.marker_pos = self.marker_pos + dt
        if translate:
            vb = self.plot.getViewBox()
            vb.translateBy((dt, 0))

    def zoom_to_marker(self):
        t_marker = self.marker_pos
        self.zoom(pos=t_marker)

    def zoom(self, pos=None, display_range=None):
        """
        Zooms to position *pos* with zoom level *zoom*. If either parameter is
        not specified, the current value for that parameter will be used

        :param pos: Position to zoom to
        :type pos: float
        :param display_range: Zoom level
        :type display_range: DisplayRange

        """
        vb = self.plotItem.getViewBox()
        if pos is None:
            pos = vb.viewRange()[0][0]
        if display_range is None:
            display_range = self.display_range
        else:
            self._range = display_range

        vb.setXRange(pos, pos + display_range)


class SeismicityPlotWidget(TimePlotWidget):
    """
    pyqtgraph PlotWidget configured to display seismic data

    :ivar plot: :class:`ScatterPlotItem` that holds the scatter plot data

    """

    def __init__(self, parent=None, **kargs):
        super(SeismicityPlotWidget, self).__init__(parent, **kargs)
        self.plot = pg.ScatterPlotItem(size=5, pen=pg.mkPen(None),
                                       brush=pg.mkBrush(255, 255, 255, 120))
        self.addItem(self.plot)


class HydraulicsPlotWidget(TimePlotWidget):
    """
    pyqtgraph PlotWidget configured to display hydraulic data

    :ivar plot: :class:`PlotCurveItem` that holds the line plot data

    """
    def __init__(self, parent=None, **kargs):
        super(HydraulicsPlotWidget, self).__init__(parent, **kargs)
        self.plot = pg.PlotCurveItem()
        self.addItem(self.plot)


class RateForecastPlotWidget(TimePlotWidget):
    """
    pyqtgraph PlotWidget configured to display forecasted and actual seismicity
    rates.

    :ivar forecast_plot: Bar graph of forecasted _rates
    :ivar rate_plot: Actual _rates plot

    """
    def __init__(self, parent=None, **kargs):
        super(RateForecastPlotWidget, self).__init__(parent, **kargs)
        self.rate_plot = pg.PlotCurveItem()
        self.addItem(self.rate_plot)
        self.forecast_plot = None


    def set_forecast_data(self, x, y):
        # FIXME: this looks like a bug in bargraphitem (the fact that it doesn't
        # allow initialization without data
        if self.forecast_plot is not None:
            self.removeItem(self.forecast_plot)
        self.forecast_plot = pg.BarGraphItem(x0=x, height=y, width=3600*6,
                                             brush=(205, 72, 66, 100),
                                             pen=(205, 72, 66, 150))
        self.addItem(self.forecast_plot)