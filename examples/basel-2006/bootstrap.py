"""
Bootstrap the Basel (2006) project
"""

import argparse

from datetime import datetime

from ramsis.datamodel.forecast import (  # noqa
    Forecast, ForecastScenario, ForecastStage, SeismicityForecastStage,
    SeismicitySkillStage, HazardStage, RiskStage)
from ramsis.datamodel.hydraulics import (  # noqa
    Hydraulics, InjectionPlan, HydraulicSample)
from ramsis.datamodel.model import Model, ModelRun  # noqa
from ramsis.datamodel.project import Project  # noqa
from ramsis.datamodel.seismicity import (  # noqa
    SeismicityModel, SeismicityModelRun, ReservoirSeismicityPrediction,
    SeismicityPredictionBin)
from ramsis.datamodel.seismics import SeismicCatalog, SeismicEvent  # noqa
from ramsis.datamodel.settings import ProjectSettings  # noqa
from ramsis.datamodel.status import Status  # noqa
from ramsis.datamodel.well import InjectionWell, WellSection  # noqa

from RAMSIS.core.builder import (
    default_project, default_forecast, default_scenario)
from RAMSIS.core.store import Store
from RAMSIS.io.hydraulics import HYDWSBoreholeHydraulicsDeserializer
from RAMSIS.io.seismics import QuakeMLCatalogDeserializer

PATH_SEISMICS = 'seismics.qml'
# Only ~this many files can be imported and merged before
# memory error occurs.
PATHS_HYDRAULICS = [
    'hyd/basel-2006-00.json',
    'hyd/basel-2006-01.json',
    'hyd/basel-2006-02.json',
    'hyd/basel-2006-03.json',
    'hyd/basel-2006-04.json',
    'hyd/basel-2006-05.json',
    'hyd/basel-2006-06.json',
    'hyd/basel-2006-07.json',
    'hyd/basel-2006-08.json',
    'hyd/basel-2006-09.json',
    'hyd/basel-2006-10.json',
    'hyd/basel-2006-11.json',
    'hyd/basel-2006-12.json',
    'hyd/basel-2006-13.json',
    'hyd/basel-2006-14.json',
    'hyd/basel-2006-15.json',
    'hyd/basel-2006-16.json',
    'hyd/basel-2006-17.json',
    'hyd/basel-2006-18.json',
    'hyd/basel-2006-19.json',
    'hyd/basel-2006-20.json',
    'hyd/basel-2006-21.json',
    'hyd/basel-2006-22.json']
#    'hyd/basel-2006-23.json',
#    'hyd/basel-2006-24.json',
#    'hyd/basel-2006-25.json',
#    'hyd/basel-2006-26.json',
#    'hyd/basel-2006-27.json',
#    'hyd/basel-2006-28.json',
#    'hyd/basel-2006-29.json',
#    'hyd/basel-2006-30.json',
#    'hyd/basel-2006-31.json',
#    'hyd/basel-2006-32.json',
#    'hyd/basel-2006-33.json',
#    'hyd/basel-2006-34.json',
#    'hyd/basel-2006-35.json',
#    'hyd/basel-2006-36.json',
#    'hyd/basel-2006-37.json',
#    'hyd/basel-2006-38.json',
#    'hyd/basel-2006-39.json', ]

PATH_INJECTION_PLAN = 'injectionplan-mignan.json'

PROJECT_STARTTIME = datetime(2006, 12, 2)
PROJECT_ENDTIME = None

FORECAST_STARTTIME = PROJECT_STARTTIME
FORECAST_ENDTIME = datetime(2006, 12, 8, 11, 33)

# NOTE(sarsonl): Reservoir definition containing all seismic events.
RESERVOIR = ('POLYHEDRALSURFACE Z ((('
             '47.58 7.59 -20000,47.58 7.6 -20000,47.592 7.6 -20000,'
             '47.592 7.59 -20000,47.58 7.59 -20000)),'
             '((47.58 7.59 -20000,47.58 7.6 -20000,'
             '47.58 7.6 0,47.58 7.59 0,47.58 7.59 -20000)),'
             '((47.58 7.59 -20000,47.592 7.59 -20000,'
             '47.592 7.59 0,47.58 7.59 0,47.58 7.59 -20000)),'
             '((47.592 7.6 0,47.592 7.59 0,47.58 7.59 0,'
             '47.58 7.6 0,47.592 7.6 0)),'
             '((47.592 7.6 0,47.592 7.59 0,47.592 7.59 -20000,'
             '47.592 7.6 -20000,47.592 7.6 0)),'
             '((47.592 7.6 0,47.592 7.6 -20000,47.58 7.6 -20000,'
             '47.58 7.6 0,47.592 7.6 0)))')


def create_models():
    URL_EM1 = 'http://localhost:5000'
    EM1_SFMWID = 'EM1'
    HOUR_IN_SECS = 3600
    DAY_IN_SECS = 86400
    HIGH_EVENT_THRESH = 100
    LOW_EVENT_THRESH = 10

    # NOTE(sarsonl): "em1_training_epoch_duration" is optional and defaults to
    # None in the model if not provided. This means the model trains for the
    # maximum length of time possible from data provided, which is the time
    # between first and last hydraulic sample with with positive topflow.

    base_config = {"em1_training_events_threshold": LOW_EVENT_THRESH,
                   "em1_training_magnitude_bin": 0.1,
                   "em1_threshold_magnitude": 0}

    retval = []

    m = SeismicityModel(
        name='EM1-Full-Training-Low-Event-Threshold',
        config=base_config,
        sfmwid=EM1_SFMWID,
        enabled=True,
        url=URL_EM1)
    retval.append(m)

    m = SeismicityModel(
        name='EM1-Hour-Moving-Window-Low-Event-Threshold',
        config={**base_config,
                **{"em1_training_epoch_duration": HOUR_IN_SECS}},
        sfmwid=EM1_SFMWID,
        enabled=True,
        url=URL_EM1)
    retval.append(m)

    m = SeismicityModel(
        name='EM1-Day-Moving-Window-Low-Event-Threshold',
        config={**base_config,
                **{"em1_training_epoch_duration": DAY_IN_SECS}},
        sfmwid=EM1_SFMWID,
        enabled=True,
        url=URL_EM1)
    retval.append(m)

    m = SeismicityModel(
        name='EM1-Full-Training-High-Event-Threshold',
        config={**base_config,
                **{"em1_training_events_threshold": HIGH_EVENT_THRESH}},
        sfmwid=EM1_SFMWID,
        enabled=True,
        url=URL_EM1)
    retval.append(m)

    m = SeismicityModel(
        name='EM1-Hour-Moving-Window-High-Event-Threshold',
        config={**base_config,
                **{"em1_training_epoch_duration": HOUR_IN_SECS,
                   "em1_training_events_threshold": HIGH_EVENT_THRESH}},
        sfmwid=EM1_SFMWID,
        enabled=True,
        url=URL_EM1)
    retval.append(m)

    m = SeismicityModel(
        name='EM1-Day-Moving-Window-High-Event-Threshold',
        config={**base_config,
                **{"em1_training_epoch_duration": DAY_IN_SECS,
                   "em1_training_events_threshold": HIGH_EVENT_THRESH}},
        sfmwid=EM1_SFMWID,
        enabled=True,
        url=URL_EM1)
    retval.append(m)

    return retval


def parse_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'db_url', type=str, metavar='URL',
        help=('DB URL indicating the database dialect and connection '
              'arguments.'))

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_cli()

    store = Store(args.db_url)

    # create models
    models = create_models()
    for m in models:
        store.add(m)

    # FIXME(damb): The project and deserializers are configured without any
    # srid. As a consequence, no transformation is performed when importing
    # data.

    # import seismic catalog
    deserializer = QuakeMLCatalogDeserializer(proj=None)
    with open(PATH_SEISMICS, 'rb') as ifd:
        cat = deserializer.load(ifd)

    # import hydraulics
    well = InjectionWell()
    deserializer = HYDWSBoreholeHydraulicsDeserializer(proj=None)
    for fpath in PATHS_HYDRAULICS:

        with open(fpath, 'rb') as ifd:
            tmp = deserializer.load(ifd)

        well.merge(tmp)

    # create project
    project = default_project(
        name='Basel 2006',
        description='Basel Project 20056',
        starttime=PROJECT_STARTTIME,
        endtime=PROJECT_ENDTIME)
    # configure project: project settings

    project.seismiccatalog = cat
    project.wells = [well]

    # create forecast
    fc = default_forecast(store, starttime=FORECAST_STARTTIME,
                          endtime=FORECAST_ENDTIME,
                          num_scenarios=0,
                          name='Basel Forecast')

    # add exemplary scenario
    scenario = default_scenario(store, name='Basel Scenario')
    scenario.reservoirgeom = RESERVOIR

    deserializer = HYDWSBoreholeHydraulicsDeserializer(
        plan=True, proj=None)
    with open(PATH_INJECTION_PLAN, 'rb') as ifd:
        scenario.well = deserializer.load(ifd)

    store.add(project)
    store.add(fc)
    store.add(scenario)
    try:
        store.save()
    except Exception:
        store.session.rollback()
        raise
    finally:
        store.close()
