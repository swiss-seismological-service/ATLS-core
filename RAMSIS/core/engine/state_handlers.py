import prefect
from time import time, sleep
from prefect.engine.result import NoResultType
from PyQt5.QtCore import pyqtSignal, QObject, QRunnable, pyqtSlot
from ramsis.datamodel.status import EStatus
from ramsis.datamodel.seismicity import SeismicityModelRun
from ramsis.datamodel.hazard import HazardModelRun
from ramsis.datamodel.forecast import EStage, Forecast

class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        # Timeout for a worker to wait for the synchronous thread to be released
        self.timeout = 1000

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        synchronous_thread = self.kwargs.pop('synchronous_thread', None)
        if synchronous_thread is not None:
            timeout = time() + self.timeout
            while synchronous_thread.is_reserved():
                sleep(1)
                if time() > timeout:
                    raise TimeoutError(
                        "Synchronous thread task taking too long to complete")
                    break
            synchronous_thread.reserve_thread()
        self.fn(*self.args, **self.kwargs)
        if synchronous_thread is not None:
            synchronous_thread.release_thread()



class BaseHandler(QObject):
    """
    Handles status changes and results emitted from prefect
    flows. SQLalchemy model objects that are returned are
    merged back into the database and pyqt signals alert the
    GUI to display changes.

    This class is initialized at the same time as the Engine,
    so the session is attached later.

    Prefect status handlers follow the form:
    :param obj: The task that the status update is from
    :param old_state: prefect.engine.state
    :param new_state: prefect.engine.state
    """
    execution_status_update = pyqtSignal(object)
    forecast_status_update = pyqtSignal(object)

    def __init__(self, threadpool, synchronous_thread):
        super().__init__()
        self.session = None
        self.threadpool = threadpool
        self.synchronous_thread = synchronous_thread

    def update_db(self):
        if self.session.dirty:
            self.session.commit()
        self.session.remove()

    def commit(self):
        if self.session.dirty:
            self.session.commit()

    def session_remove(self):
        self.session.remove()

    def state_evaluator(self, new_state, func_list):
        conditions_met = True
        for func in func_list:
            if not func(new_state):
                conditions_met = False
        return conditions_met

    def task_finished(self, new_state):
        conditions_met = False
        if (new_state.is_finished() and not
            new_state.is_skipped() and not
            new_state.is_mapped() and not
                new_state.is_looped()):
            conditions_met = True
        return conditions_met

    def successful_result(self, new_state):
        conditions_met = False
        if (new_state.is_successful() and not
                isinstance(new_state.result, NoResultType)):
            conditions_met = True
        return conditions_met

    def error_result(self, new_state):
        conditions_met = False
        if (new_state.is_failed() and not
                isinstance(new_state.result, NoResultType)):
            conditions_met = True
        return conditions_met




class ForecastHandler(BaseHandler):
    """
    Handles status changes and results emitted from prefect
    flows. SQLalchemy model objects that are returned are
    merged back into the database and pyqt signals alert the
    GUI to display changes.

    This class is initialized at the same time as the Engine,
    so the session is attached later.

    Prefect status handlers follow the form:
    :param obj: The task that the status update is from
    :param old_state: prefect.engine.state
    :param new_state: prefect.engine.state
    """
    @staticmethod
    def scenario_stage_status(scenario):
        # If all model runs are complete without error, then the
        stage = scenario[EStage.SEISMICITY]
        # stage is a success
        model_success = all([
            True if model.status.state == EStatus.COMPLETE else False
            for model in [r for r in stage.runs if r.enabled]])
        if model_success:
            stage.status.state = EStatus.COMPLETE
        else:
            stage.status.state = EStatus.ERROR

        # If all stages are complete without error, then the
        # scenario is a success
        stage_states = [stage.status.state for stage in
                        [s for s in scenario.stages if s.enabled]]
        if all([state == EStatus.COMPLETE
                for state in stage_states]):
            scenario.status.state = EStatus.COMPLETE
        elif any([state == EStatus.ERROR
            for state
            in stage_states]):
            scenario.status.state = EStatus.ERROR
        elif any([state == EStatus.PENDING
                 for state in stage_states]):
            scenario.status.state = EStatus.RUNNING

        return scenario

    def flow_state_handler(self, obj, old_state, new_state):
        """
        Set the forecast state according to the end state
        of the flow.
        """
        logger = prefect.context.get("logger")
        forecast_id = prefect.context.forecast_id
        worker = Worker(self.update_seismicity_statuses, new_state, logger,
                        forecast_id,
                        synchronous_thread=self.synchronous_thread)
        forecast = self.session.query(Forecast).first()
        plan_section = forecast.scenarios[0].well.sections[0]
        topz = plan_section.topz_value
        bottomz = plan_section.bottomz_value
        self.session.remove()
        self.threadpool.start(worker)

    def update_seismicity_statuses(self, new_state, logger, forecast_id):
        forecast = self.session.query(Forecast).filter(
            Forecast.id == forecast_id).first()

        if new_state.is_running():
            forecast.status.state = EStatus.RUNNING
            for scenario in forecast.scenarios:
                if scenario.enabled:
                    scenario.status.state = EStatus.RUNNING
            self.update_db()

        elif new_state.is_finished():
            for scenario in forecast.scenarios:
                scenario = self.scenario_stage_status(scenario)

            self.update_db()
        forecast = self.session.query(Forecast).first()
        plan_section = forecast.scenarios[0].well.sections[0]
        topz = plan_section.topz_value
        bottomz = plan_section.bottomz_value
        self.session.remove()
        return new_state

    def scenario_models_state_handler(self, obj, old_state, new_state):
        """
        Set the model runs status to RUNNING when this task suceeds.
        """
        if self.state_evaluator(new_state, [self.task_finished,
                                            self.successful_result]):
            model_runs = new_state.result
            for run in model_runs:
                run.status.state = EStatus.RUNNING
                self.session.commit()
            self.update_db()
        return new_state

    def model_run_state_handler(self, obj, old_state, new_state):
        """
        The seismicity model run task sends a Sucessful state
        when the remote model worker has accepted a task.
        A Failed state is sent from the task otherwise.

        A pyqt signal will be sent on success or failure of the task.
        """
        logger = prefect.context.get("logger")

        if self.state_evaluator(new_state, [self.task_finished]):
            worker = Worker(self.dispatched_model_run, new_state, logger)
            self.threadpool.start(worker)
        return new_state

    def dispatched_model_run(self, new_state, logger):
        if self.state_evaluator(new_state, [self.successful_result]):
            model_run = new_state.result

            update_model_run = self.session.query(SeismicityModelRun).\
                filter(SeismicityModelRun.id == model_run.id).first()
            update_model_run.runid = model_run.runid
            logger.info(f"Model run with runid={model_run.runid}"
                        "has been dispatched to the remote worker.")
            update_model_run.status.state = model_run.status.state
        elif self.state_evaluator(new_state, [self.error_result]):
            # prefect Fail should be raised with model_run as a result
            logger.warning(f"Model run has failed: {new_state.result}. "
                           f"Message: {new_state.message}")
            model_run = new_state.result
            update_model_run = self.session.query(SeismicityModelRun).\
                filter(SeismicityModelRun.id == model_run.id).first()
            update_model_run.status.state = EStatus.ERROR

        # The sent status is not used, as the whole scenario must
        # be refreshed from the db in the gui thread.
        
        self.update_db()
        self.execution_status_update.emit((
            new_state, type(model_run),
            model_run.id))
        

    def poll_seismicity_state_handler(self, obj, old_state, new_state):
        """
        The polling task sends a Sucessful state when the remote
        model worker has returned a forecast and this has been
        deserialized sucessfully. A Failed state is sent from the
        task otherwise.
        A pyqt signal will be sent on success or failure of the task.
        """
        # sarsonl: pass logger from the context in the main thread
        forecast = self.session.query(Forecast).first()
        plan_section = forecast.scenarios[0].well.sections[0]
        topz = plan_section.topz_value
        bottomz = plan_section.bottomz_value
        self.session.remove()
        logger = prefect.context.get("logger")

        if self.state_evaluator(new_state, [self.task_finished]):
            if self.state_evaluator(new_state, [self.successful_result]):
                model_run, model_result = new_state.result
                logger.info(f"Model with runid={model_run.runid} "
                            "has returned without error from the "
                            "remote worker.")
                update_model_run = self.session.query(SeismicityModelRun).\
                    filter(SeismicityModelRun.id == model_run.id).first()
                update_model_run.status.state = EStatus.COMPLETE
                self.update_db()
                worker = Worker(self.finished_model_run, new_state, logger,
                                synchronous_thread=self.synchronous_thread)
                self.threadpool.start(worker)

            elif self.state_evaluator(new_state, [self.error_result]):
                model_run = new_state.result
                logger.error(f"Model with runid={model_run.runid}"
                             "has returned an error from the "
                             "remote worker.")
                update_model_run = self.session.query(SeismicityModelRun).\
                    filter(SeismicityModelRun.id == model_run.id).first()
                update_model_run.status.state = EStatus.ERROR
                self.update_db()
            self.execution_status_update.emit((
                new_state, type(model_run),
                model_run.id))
        forecast = self.session.query(Forecast).first()
        plan_section = forecast.scenarios[0].well.sections[0]
        topz = plan_section.topz_value
        bottomz = plan_section.bottomz_value
        self.session.remove()
        return new_state

    def finished_model_run(self, new_state, logger):
        """
        Adding the result to the database may take time and as this task
        being completed in a timely fashion does not impact the flow, this
        can be moved to another thread.
        """
        model_run, model_result = new_state.result
        update_model_run = self.session.query(SeismicityModelRun).\
            filter(SeismicityModelRun.id == model_run.id).first()
        update_model_run.result = model_result
        self.update_db()

    def add_catalog(self, new_state, logger):
        forecast = new_state.result
        # A forecast may only have one seismiccatalog associated
        # This is enforced in code rather than at db level.
        assert(len(forecast.seismiccatalog) == 1)
        if forecast.seismiccatalog[0] not in self.session():
            self.session.add(forecast.seismiccatalog[0])
            self.session.commit()
            self.session.merge(forecast)
            self.update_db()
            logger.info(f"Forecast id={forecast.id} has made a snapshot"
                        " of the seismic catalog")
        else:
            logger.info(f"Forecast id={forecast.id} already has a snapshot"
                        " of the seismic catalog. "
                        "No new snapshot is being made.")
        self.session.remove()

    def catalog_snapshot_state_handler(self, obj, old_state, new_state):
        """
        When the catalog snapshot task has been skipped, then the forecast
        already has a catalog snapshot and this is not overwritten.
        If this task has completed successfully, the new snapshot is added
        to the session and forecast merged as an attribute was modified.
        """
        logger = prefect.context.get("logger")
        if self.state_evaluator(new_state, [self.task_finished,
                                            self.successful_result]):

            worker = Worker(self.add_catalog, new_state, logger,
                            synchronous_thread=self.synchronous_thread)
            self.threadpool.start(worker)
        return new_state

    def add_well(self, new_state, logger, **kwargs):
        forecast = new_state.result
        # A forecast may only have one well associated
        # This is enforced in code rather than at db level.
        assert(len(forecast.well) == 1)
        if forecast.seismiccatalog[0] not in self.session():
            self.session.add(forecast.well[0])
            self.session.commit()
            self.session.merge(forecast)
            self.update_db()
            logger.info(f"Forecast id={forecast.id} has made a snapshot"
                        " of the hydraulic well")
        else:
            logger.info(f"Forecast id={forecast.id} already has a snapshot"
                        " of the hydraulic well. "
                        "No new snapshot is being made.")
        forecast = self.session.query(Forecast).first()
        plan_section = forecast.scenarios[0].well.sections[0]
        topz = plan_section.topz_value
        bottomz = plan_section.bottomz_value

    def well_snapshot_state_handler(self, obj, old_state, new_state):
        """
        When the well snapshot task has been skipped, then the forecast
        already has a well snapshot and this is not overwritten.
        If this task has completed successfully, the new snapshot is added
        to the session and forecast merged as an attribute was modified.
        """
        logger = prefect.context.get("logger")
        if self.state_evaluator(new_state, [self.task_finished,
                                            self.successful_result]):
            worker = Worker(self.add_well, new_state, logger,
                            synchronous_thread=self.synchronous_thread)
            self.threadpool.start(worker)
        return new_state

class HazardHandler(BaseHandler):
    """
    Handles status changes and results emitted from prefect
    flows. SQLalchemy model objects that are returned are
    merged back into the database and pyqt signals alert the
    GUI to display changes.

    This class is initialized at the same time as the Engine,
    so the session is attached later.

    Prefect status handlers follow the form:
    :param obj: The task that the status update is from
    :param old_state: prefect.engine.state
    :param new_state: prefect.engine.state
    """
    @staticmethod
    def scenario_stage_status(scenario):
        # If all model runs are complete without error, then the
        stage = scenario[EStage.HAZARD]
        # stage is a success
        model_success = all([
            True if model.status.state == EStatus.COMPLETE else False
            for model in [r for r in stage.runs if r.enabled]])
        if model_success:
            stage.status.state = EStatus.COMPLETE
        else:
            stage.status.state = EStatus.ERROR

        # If all stages are complete without error, then the
        # scenario is a success
        # TODO sarsonl: need to check that not only is the stage enabled,
        # but also that there are models/model runs associated
        stage_success = all([
            True if stage.status.state == EStatus.COMPLETE else False
            for stage in [s for s in scenario.stages if s.enabled]])
        if stage_success:
            scenario.status.state = EStatus.COMPLETE
        else:
            scenario.status.state = EStatus.ERROR

        return scenario

    def flow_state_handler(self, obj, old_state, new_state):
        """
        Set the forecast state according to the end state
        of the flow.
        """
        forecast_id = prefect.context.forecast_id
        forecast = self.session.query(Forecast).filter(
            Forecast.id == forecast_id).first()

        if new_state.is_running():
            forecast.status.state = EStatus.RUNNING
            for scenario in forecast.scenarios:
                if scenario.enabled:
                    scenario.status.state = EStatus.RUNNING
            self.update_db()

        elif new_state.is_finished():
            for scenario in forecast.scenarios:
                scenario = self.scenario_stage_status(scenario)
            self.update_db()
            self.session.remove()
        return new_state

    def update_db(self):
        if self.session.dirty:
            self.session.commit()
        self.session.remove()

    def create_hazard_models_state_handler(self, obj, old_state, new_state):
        """
        """
        if self.state_evaluator(new_state, [self.task_finished,
                                            self.successful_result]):
            runs = new_state.result
            for run in runs:
                self.session.add(run)
                self.update_db()
        return new_state

    def update_hazard_models_state_handler(self, obj, old_state, new_state):
        """
        """
        logger = prefect.context.get("logger")
        if self.state_evaluator(new_state, [self.task_finished,
                                            self.successful_result]):
            runs = new_state.result
            for run in runs:
                hazard_run = self.session.query(HazardModelRun).filter(HazardModelRun.id==run.id).first()

                for seis_run in run.seismicitymodelruns:
                    update_seis_run = self.session.query(SeismicityModelRun).filter(SeismicityModelRun.id==seis_run.id).first()
                    update_seis_run.hazardruns.append(hazard_run)
                self.update_db()
        return new_state

    def model_run_state_handler(self, obj, old_state, new_state):
        """
        The seismicity model run task sends a Sucessful state
        when the remote model worker has accepted a task.
        A Failed state is sent from the task otherwise.

        A pyqt signal will be sent on success or failure of the task.
        """
        logger = prefect.context.get("logger")

        if self.state_evaluator(new_state, [self.task_finished]):
            model_runs = new_state.result
            for model_run in model_runs:
                if self.state_evaluator(new_state, [self.successful_result]):
                    update_model_run = self.session.query(HazardModelRun).\
                        filter(HazardModelRun.id == model_run.id).first()
                    update_model_run.runid = model_run.runid
                    logger.info(f"Model run with runid={model_run.runid}"
                                "has been dispatched to the remote worker.")
                    update_model_run.status.state = model_run.status.state
                elif self.state_evaluator(new_state, [self.error_result]):
                    # prefect Fail should be raised with model_run as a result
                    logger.warning(f"Model run has failed: {new_state.result}. "
                                   f"Message: {new_state.message}")
                    update_model_run = self.session.query(HazardModelRun).\
                        filter(HazardModelRun.id == model_run.id).first()
                    update_model_run.status.state = EStatus.ERROR

                # The sent status is not used, as the whole scenario must
                # be refreshed from the db in the gui thread.
                self.update_db()
                logger.info("execution status... {}".format(self.execution_status_update))
                self.execution_status_update.emit((
                    new_state, type(model_run),
                    model_run.id))
        return new_state

    def poll_hazard_state_handler(self, obj, old_state, new_state):
        """
        The polling task sends a Sucessful state when the remote
        model worker has returned a forecast and this has been
        deserialized sucessfully. A Failed state is sent from the
        task otherwise.
        A pyqt signal will be sent on success or failure of the task.
        """
        logger = prefect.context.get("logger")

        if self.state_evaluator(new_state, [self.task_finished]):
            if self.state_evaluator(new_state, [self.successful_result]):
                model_run, model_result = new_state.result
                logger.info(f"Model with runid={model_run.runid} "
                            "has returned without error from the "
                            "remote worker.")
                update_model_run = self.session.query(HazardModelRun).\
                    filter(HazardModelRun.id == model_run.id).first()
                update_model_run.status.state = EStatus.COMPLETE
                update_model_run.result = model_result

            elif self.state_evaluator(new_state, [self.error_result]):
                model_run = new_state.result
                logger.error(f"Model with runid={model_run.runid}"
                             "has returned an error from the "
                             "remote worker.")
                update_model_run = self.session.query(HazardModelRun).\
                    filter(HazardModelRun.id == model_run.id).first()
                update_model_run.status.state = EStatus.ERROR
            self.update_db()
            self.execution_status_update.emit((
                new_state, type(model_run),
                model_run.id))
        return new_state