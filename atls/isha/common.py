# -*- encoding: utf-8 -*-
"""
Common stuff for all ISHA models such as the parent class and the data
structures that are required to interact with the model.
    
Copyright (C) 2013, ETH Zurich - Swiss Seismological Service SED

"""

from PyQt4 import QtCore
from datetime import datetime
from datetime import timedelta
from collections import namedtuple
from modelvalidation import log_likelihood
import logging

class ModelInput(object):
    """
    Holds ISHA model inputs and parameters for the next run. Not all models may
    require all of the inputs.

    :ivar forecast_mag_range: Tuple that specifies Mmin, Mmax for the forecast
    :type forecast_mag_range: Tuple with two floats
    :ivar seismic_events: List of recorded seismic events
    :type seismic_events: List of SeismicEvent objects
    :ivar hydraulic_events: List of recorded hydraulic events
    :type hydraulic_events: List of HydraulicEvent objects
    :ivar forecast_times: List of times (datetime) at which to forecast
    :type forecast_times: List of datetime objects
    :ivar t_bin: Forecast bin size in hours. The default is 6h.
    :type t_bin: float
    :ivar expected_flow: Expected flow rate during forecast [l/min]
    :type expected_flow: float
    :ivar mc: Magnitude of completeness
    :type mc: float

    """
    _data_attrs = ['t_run', 'forecast_mag_range', 'seismic_events',
                   'hydraulic_events', 'forecast_times', 't_bin',
                   'injection_well', 'expected_flow', 'mc']

    def __init__(self, t_run, project=None, bin_size=6.0, mc=None,
                 mag_range=None):
        """
        Create input for a model run.

        :param t_run: time of the run (serves as an identifier)
        :type t_run: datetime
        :param project: atls project containing the data
        :type project: AtlsProject
        :param bin_size: size of the forecast bin [hours]
        :type bin_size: float
        :param num_bins: number of forecasts to make (usually 1)
        :type num_bins: int
        :param mc: magnitude of completeness
        :type mc: float
        :param mag_range: tuple of two specifying the forecast magnitude range
        :type num_bins: tuple

        """
        dt = timedelta(hours=bin_size)
        self.t_run = t_run
        self.forecast_mag_range = mag_range
        self.mc = mc
        # TODO: list is legacy (no more support for multiple fc times)
        self.forecast_times = [t_run]
        self.injection_well = None
        self.expected_flow = None
        self.t_bin = bin_size
        if project:
            self.hydraulic_events = \
                project.hydraulic_history.events_before(t_run)
            self.seismic_events = \
                project.seismic_history.events_before(t_run)
            self.injection_well = project.injection_well
        else:
            self.seismic_events = None
            self.hydraulic_events = None

    def estimate_expected_flow(self, t_run, project, bin_size=6.0):
        """
        Compute expected flow from (future) data.

        The expected flow during the forecast period is computed as the average
        from the flow samples for that period. If no data is available, zero
        flow is assumed.

        :param project: atls project containing the data
        :param t_run: time of the run
        :param bin_size: size of the forecast bin(s) [hours]

        """
        t_fc = bin_size * 60
        t_end = t_run + timedelta(minutes=t_fc)
        events = project.hydraulic_history.events_between(t_run, t_end)
        if len(events) == 0:
            self.expected_flow = 0
        else:
            # TODO: we might have to estimate this from flow_dh. Also, the
            # current implementation does not handle irregularly spaced samples
            # correctly.
            self.expected_flow = sum([e.flow_xt for e in events]) / len(events)


    def primitive_rep(self):
        """
        Generator that unpacks input data into simple lists of primitive types.

        We do this since we can't pass python objects to external code such as
        Matlab. Lists are yielded as tuples (list_name, list) where list_name is
        the name of the corresponding member variable. Members of members will
        be returned with a combined name, E.g. all self.seismic_event.magnitude
        will be returned as a list named *seismic_event_magnitude*. datetime
        objects translated into unix time stamps

        """
        for base_name in ModelInput._data_attrs:
            attr = getattr(self, base_name)
            # make everything into a sequence type first
            if attr is None:
                attr = []
            elif not hasattr(attr, '__iter__'):
                attr = [attr]
            if len(attr) > 0 and hasattr(attr[0], 'data_attrs'):
                for attr_name in attr[0].data_attrs:
                    combined_name = base_name + '_' + attr_name
                    data = [getattr(obj, attr_name) for obj in attr]
                    yield combined_name, _primitive(data)
            else:
                yield base_name, _primitive(attr)


class Rating(object):
    """ Forecast validation (Model performance score) """
    def __init__(self, LL):
        """
        :param LL: log likelihood

        """
        self.LL = LL


class ForecastResult(object):
    """ Result container for a single forecast """
    def __init__(self, rate, prob, region=None):
        """
        :param rate: forecast rate
        :param prob: forecast probability of one or more events occurring
        :param region: region for which the forecast is valid (a Cube)
        :param score: Score for the forecast result

        """
        self.rate = rate
        self.prob = prob
        self.region = region
        self.score = None


class ModelOutput:
    """
    Models store their output into this container structure.

    :ivar spatial_results: an (optional) list containing the forecast results
        for each forecast region in a spatial model.
    :ivar result: cumulative result for the entire forecast region
    :type result: ForecastResult
    :ivar model: a reference to the model that created the forecast
    :ivar t_run: time of the forecast
    :type t_run: datetime
    :ivar dt: forecast period duration [hours]
    :type dt: timedelta
    :ivar has_results: false if the model did not produce any results
    :ivar no_results_reason: a reason given by the model for not producing any
        results.

    """
    def __init__(self, t_run, dt, model):
        self.has_results = True
        self.no_result_reason = 'Unknown'
        self.t_run = t_run
        self.dt = dt
        self.model = model
        self.spatial_results = None
        self.result = None
        self._reviewed = False

    @property
    def reviewed(self):
        return self._reviewed

    def compute_cumulative(self):
        """
        Computes the cumulative result from the individual spatial results.

        """
        rate = reduce(lambda x, y: x+y, [r.review for r in self.spatial_results])
        prob = reduce(lambda x, y: x+y, [r.prob for r in self.spatial_results])
        self.result = ForecastResult(rate=rate, prob=prob)

    def review(self, observations):
        """
        Reviews results based on the 'truth' data in event **observations** for
        the forecast period and assigns a score to the model.

        :param observations: the observed events for the forecast period
        :type observations: list of SeismicEvent objects

        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        if self.spatial_results is not None:
            for result in self.spatial_results:
                region = result.region
                obs = len([e for e in observations if e.in_region(region)])
                result.rating = Rating(LL=log_likelihood(result.review, obs))
        LL = log_likelihood(self.result.rate, len(observations))
        self.result.score = Rating(LL=LL)
        self._reviewed = True
        logger.debug('{} at {}: LL = {}'.format(self.model.title,
                                                self.t_run,
                                                self.result.score.LL))

class ModelState:
    IDLE = 0
    RUNNING = 1


class Model(QtCore.QObject):
    """
    Abstract model class that provides the common functionality for ISHA
    forecast models

    .. pyqt4:signal:finished: emitted when the model has finished its run
    successfully and has new run results. Carries the output as payload.
    .. pyqt4:signal:state_changed: emitted when the model changes its state
    from running to idle or vice versa

    :ivar output: output of the last run
    :ivar title: display title of the model

    """

    # If set to true, any model errors will raise an exception
    RAISE_ON_ERRORS = True

    finished = QtCore.pyqtSignal(object)
    state_changed = QtCore.pyqtSignal(object)

    def __init__(self):
        """ Initializes the model """
        super(Model, self).__init__()
        self._model_input = None
        self.output = None
        self.title = 'Model'
        self._state = ModelState.IDLE
        self._logger = logging.getLogger(self.__class__.__name__)

    @property
    def model_input(self):
        return self._model_input

    def prepare_run(self, model_input):
        """
        Prepares the model for the next run. The data that is required for the
        run is supplied in *model_input*

        :param model_input: data for the next run
        :type model_input: ModelInput

        """
        self._model_input = model_input

    def run(self):
        """
        Invoked when the model should perform a run. This method takes care of
        state changes and emitting signals as required. The actual model code
        is run from _do_run.

        """
        self._logger.info(self.title + ' model run initiated')
        self.state = ModelState.RUNNING
        self.output = self._do_run()
        self.finished.emit(self.output)
        self._logger.info(self.title + ' model run completed')
        self.state = ModelState.IDLE

    def _do_run(self):
        """
        Abstract method to run the actual model code.

        You should Override this function in a subclass and return the results
        for the run in model output if successful. If the model produces no
        results for a particular run, return a resultless output.

        """
        pass

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state
        self.state_changed.emit(state)

    # Some helper functions

    def flow_rate_in_interval(self, t_min, t_max):
        """
        Returns the flow rate from run input that is representative for the
        interval t_min, t_max.

        The function returns the maximum flow rate in the time interval
        [t_min, t_max]. If no flow rate data is available in this interval, it
        returns the last flow rate it finds.

        If no flow rates are present at all the function returns 0

        """
        if self._model_input.hydraulic_events is None:
            return 0
        rates = [h.flow_dh for h in self._model_input.hydraulic_events
                 if t_min <= h.date_time < t_max]
        if len(rates) == 0:
            last_flow = self._model_input.hydraulic_events[-1]
            flow = last_flow.flow_dh
        else:
            flow = max(rates)
        return flow


def _primitive(attr):
        """ Converts any datetime object to unix time stamp """
        epoch = datetime(1970, 1, 1)
        if len(attr) > 0 and isinstance(attr[0], datetime):
            return [(dt - epoch).total_seconds() for dt in attr]
        else:
            return attr