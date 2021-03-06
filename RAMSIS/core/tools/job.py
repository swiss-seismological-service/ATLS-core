# -*- coding: utf-8 -*-
"""
Base classes for parallel or serial execution of work work_units

Jobs can be nested or, i.e. a job can act as a work_unit for another job.
Jobs and work units emit status_changed signals when something changes.
All notifications must be fowarded up the job chain and carry the respective
*Status* payload.

Copyright (c) 2017, Swiss Seismological Service, ETH Zurich

"""

from PyQt5.QtCore import QObject, pyqtSignal


class JobStatus:
    """ 
    Status change notification for status_changed signals 
    
    :param WorkUnit or Job sender: Sender
    :param finished: True if the work unit has finished (successful or not)
    :param info: Additional info such as a http response
    
    """
    def __init__(self, sender, finished=False, info=None):
        self.sender = sender
        self.finished = finished
        self.info = info


class Job(QObject):
    """
    Abstract base class for a job

    :ivar dict shared_data: Shared data between work units and the job. The
        attribute is typically used to share input and output data, however
        it is completely up to the work units what to do with it.
    :ivar [WorkUnit] work_units: list of work units for this job

    :param str job_id: an id for this job


    """

    status_changed = pyqtSignal(object)

    def __init__(self, job_id):
        super(Job, self).__init__()
        self.job_id = job_id
        self._work_units = []

    @property
    def work_units(self):
        return self._work_units

    @work_units.setter
    def work_units(self, work_units):
        self._work_units = work_units
        for unit in work_units:
            unit.status_changed.connect(self.on_status_changed)

    def pre_process(self):
        pass

    def post_process(self):
        pass

    def on_status_changed(self, status):
        # forward the notification up the chain
        self.status_changed.emit(status)


class SerialJob(Job):
    """
    A job that executes its work units in sequence

    The next unit is only started when the previous unit has
    sent a *status_change* signal with finished=True. The serial jobs own
    status_changed signal is emitted after the last unit has completed.

    """

    def __init__(self, job_id):
        super(SerialJob, self).__init__(job_id)
        self._iter = None

    def run(self):
        self._iter = iter(self.work_units)
        self.pre_process()
        self._run_next()

    def on_status_changed(self, status):
        super(SerialJob, self).on_status_changed(status)
        if status.sender in self.work_units and status.finished:
            self._run_next()

    def _run_next(self):
        try:
            work_unit = next(self._iter)
        except StopIteration:
            self._iter = None
            self.post_process()
            self.status_changed.emit(JobStatus(self, finished=True))
        else:
            work_unit.run()


class ParallelJob(Job):
    """
    A job that executes its work units in parallel

    All work units are started concurrently. The job's *status_changed*
    signal is emitted with finished=True when all work units have sent their 
    finished signal.

    """

    def __init__(self, job_id):
        super(ParallelJob, self).__init__(job_id)
        self._completed_units = []

    def run(self):
        self._completed_units = []
        self.pre_process()
        for unit in self.work_units:
            unit.run()

    def on_status_changed(self, status):
        super(ParallelJob, self).on_status_changed(status)
        if status.sender in self.work_units and status.finished:
            self._completed_units.append(status.sender)
            if len(self.work_units) == len(self._completed_units):
                self.post_process()
                self.status_changed.emit(JobStatus(self, finished=True))


class WorkUnit(QObject):
    """
    A unit of work within a job

    Override run in the subclass and make sure to emit the 
    *status_changed* signal at the end of *run* and pass self together
    with finished=True.

    """

    status_changed = pyqtSignal(object)

    def __init__(self, job_id):
        super(WorkUnit, self).__init__()
        self.job_id =job_id

    def run(self):
        pass
