# -*- encoding: utf-8 -*-
"""
Short Description

Long Description

Copyright (C) 2013, ETH Zurich - Swiss Seismological Service SED

"""

import logging
from math import log, factorial

from sqlalchemy import Column, Integer, Float, DateTime, Boolean, String, \
    ForeignKey
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm import relationship, backref

from ormbase import OrmBase


def log_likelihood(forecast, observation):
    """
    Compute the log likelihood of an observed rate given a forecast

    The forecast value is interpreted as expected value of a poisson
    distribution. The function expects scalars or numpy arrays as input. In the
    latter case it computes the LL for each element.

    :param forecast: forecast rate
    :param observations: observed rate
    :return: log likelihood for each element of the input

    """
    ll = -forecast + observation * log(forecast) - log(factorial(observation))
    return ll


class ISForecastResult(OrmBase):
    """
    Results of one IS forecast run

    ISForecastResult holds the results from individual IS forecast models in
    *model_results*. The member *model_results* is a dict of the form

    model_results = {
        'etas': model_result,
        'rj': model_result,
        ...
    }

    """

    # ORM declarations
    __tablename__ = 'isforecastresult'
    id = Column(Integer, primary_key=True)
    t_run = Column(DateTime)
    _reviewed = Column('reviewed', Boolean)
    model_results = relationship('ISModelResult', backref='isforecastresult',
                                 collection_class=attribute_mapped_collection('model_name'),
                                 cascade="all, delete-orphan")

    def __init__(self, t_run):
        """
        :param t_run: time of the model run
        :type t_run: datetime

        """
        self.t_run = t_run
        self._reviewed = False
        self.model_results = {}

    @property
    def reviewed(self):
        return self._reviewed

    def review(self, observed_events):
        for result in self.model_results.itervalues():
            result.review(observed_events)
        self._reviewed = True


class ISModelResult(OrmBase):
    """
    Output resulting from IS forecast run for one specific IS model. The output
    either contains a result or a reason why no result is available.

    :ivar model_name: a reference to the model that created the forecast
    :ivar t_run: time of the forecast
    :type t_run: datetime
    :ivar dt: forecast period duration [hours]
    :type dt: float
    :ivar failed: true if the model did not produce any results
    :ivar failure_reason: a reason given by the model for not producing any
        results.
    :ivar cum_result: cumulative forecast result
    :type cum_result: ISResult
    :ivar vol_results: volumetric results (per voxel)
    :type vol_results: list[ISResult]

    """

    # ORM declarations
    __tablename__ = 'ismodelresult'
    id = Column(Integer, primary_key=True)
    model_name = Column(String)
    failed = Column(Boolean)
    failure_reason = Column(String)
    t_run = Column(DateTime)
    dt = Column(Float)

    # Configures the one-to-one relationship for the cumulative result
    # use_alter=True along with name='' adds this foreign key after ISResult
    # has been created to avoid circular dependency
    cum_result_id = Column(Integer, ForeignKey('isresult.id', use_alter=True,
                                               name='fk_cum_result_id'))
    # set post_update=True to avoid circular dependency during
    cum_result = relationship('ISResult', foreign_keys=cum_result_id,
                              post_update=True, cascade="all, delete-orphan",
                              single_parent=True)

    forecast_id = Column(Integer, ForeignKey('isforecastresult.id'))
    _reviewed = Column('reviewed', Boolean)

    def __init__(self, output):
        """
        Inits an ISModelResult from a bare ModelOutput

        :param output: model output
        :type output: ModelOutput

        """
        self.model_name = output.model.title
        self.failed = output.failed
        self.failure_reason = output.failure_reason
        self.t_run = output.t_run
        self.dt = output.dt
        if output.cum_result is not None:
            self.cum_result = ISResult.from_model_result(output.cum_result)
        else:
            self.cum_result = None
        if output.vol_results is not None:
            self.vol_results = [ISResult.from_model_result(r)
                                for r in output.vol_results]
        else:
            self.vol_results = []

    @property
    def reviewed(self):
        return self._reviewed

    def compute_cumulative(self):
        """
        Computes the cumulative result from the individual spatial results.

        """
        rate = sum(r.rate for r in self.vol_results)
        # FIXME: averaging the b_val is most likely completely wrong
        b_val = sum(r.b_val for r in self.vol_results) / len(self.vol_results)
        prob = sum(r.prob for r in self.vol_results)
        self.cum_result = ISResult(rate, b_val, prob)

    def review(self, observations):
        """
        Reviews results based on the 'truth' data in event **observations** for
        the forecast period and assigns a score to the model.

        :param observations: the observed events for the forecast period
        :type observations: list of SeismicEvent objects

        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        if self.vol_results:
            # TODO: compute LL per voxel
            # at the moment we don't know the region for each volumetric
            # result.
            # for result in self.vol_results:
            #     region = result.region
            #     obs = len([e for e in observations if e.in_region(region)])
            #     result.score = log_likelihood(result.review, obs)
            pass
        self.cum_result.score = log_likelihood(self.cum_result.rate,
                                               len(observations))
        self._reviewed = True
        logger.debug('{} at {}: LL = {}'.format(self.model.title,
                                                self.t_run,
                                                self.result.score.LL))


class ISResult(OrmBase):
    """ Result container for a single forecast """

    # ORM declarations
    __tablename__ = 'isresult'
    id = Column(Integer, primary_key=True)
    rate = Column(Float)
    b_val = Column(Float)
    prob = Column(Float)
    score = Column(Float)

    # Configures the one-to-many relationship between ISModelResult's
    # vol_results and this entity
    model_result_id = Column(Integer, ForeignKey(ISModelResult.id))
    model_result = relationship(ISModelResult, foreign_keys=model_result_id,
                                backref=backref('vol_results',
                                                cascade="all, delete-orphan"))

    def __init__(self, rate, b_val, prob):
        self.prob = prob
        self.rate = rate
        self.b_val = b_val
        self.score = None

    @classmethod
    def from_model_result(cls, result):
        """
        Inits an ISResult from a bare model result

        :param result: model result
        :type result: ModelResult

        """
        return cls(result.rate, result.b_val, result.prob)
