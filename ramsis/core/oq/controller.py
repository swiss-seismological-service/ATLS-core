from subprocess import Popen, PIPE
import os
import sys
import re
import logging
import tempfile
import shutil
import utils

from PyQt4 import QtCore

# Debug settings
RAMSIS_LOG_LEVEL = logging.DEBUG
KEEP_INPUTS = False

# RAMSIS constants
ramsis_path = os.path.dirname(os.path.realpath(sys.argv[0]))
_OQ_RESOURCE_PATH = os.path.join(ramsis_path, 'resources', 'oq')
_HAZ_RESOURCES = {
    'job_def': 'job.ini',
    'gmpe_lt': 'gmpe_logic_tree.xml',
    'source': 'point_source_model.xml',
    'source_lt': 'source_model_logic_tree.xml'
}
_RISK_POE_RESOURCES = {
    'job_def': 'job.ini',
    'exp_model': 'exposure_model.xml',
    'vuln_model': 'struct_vul_model.xml'
}


class _OqRunner(QtCore.QObject):
    job_complete = QtCore.pyqtSignal(object)

    def __init__(self):
        super(_OqRunner, self).__init__()
        # input
        self.job_input = None

    def run(self):
        assert self.job_input is not None, 'No job input provided'

        job_type = self.job_input["job_type"]
        if job_type == "hazard":
            args = [
                "oq-engine",
                "--run-hazard",
                self.job_input["job_def"]
            ]
        elif job_type == "risk":
            args = [
                "oq-engine",
                "--run-risk",
                self.job_input["job_def"],
                "--hazard-calculation-id",
                str(self.job_input["hazard_calculation_id"])
            ]
        else:
            raise RuntimeError("No valid job type provided")

        proc = Popen(args, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        exitcode = proc.returncode
        job_id = self._process_oq_output(out, err, exitcode)
        self.job_complete.emit(job_id)

    def _process_oq_output(self, out, err, exitcode):
        error_message = 'Could not retrieve results from OpenQuake'

        if exitcode != 0:
            raise RuntimeError(error_message)

        pattern = 'Calculation ([0-9]+) completed in [0-9]+ seconds. Results:'
        m = re.search(pattern, out)
        if not m:
            raise RuntimeError(error_message)

        job_id = int(m.group(1))
        return job_id


class _OqController(QtCore.QObject):
    def __init__(self):
        super(_OqController, self).__init__()
        # Setup the OQ listener thread and move the OQ runner object to it
        self._oq_thread = QtCore.QThread()
        self._oq_thread.setObjectName('OQ')
        self._oq_runner = _OqRunner()
        self._oq_runner.moveToThread(self._oq_thread)
        self._oq_thread.started.connect(self._oq_runner.run)
        self._oq_runner.job_complete.connect(self._job_complete)

        # internal vars
        self.busy = False
        self.callback = None
        self.job_dir = None
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(RAMSIS_LOG_LEVEL)

    def run_hazard(self, source_params, callback):
        """
        Run a OQ hazard job

        OQ hazard jobs run asynchronously and invoke *callback* on completion.
        The result of the run is simply a job id that can be used to fetch the
        actual results from the OQ database.

        :param source_params: dictionary Gutenberg-Richter a,b values and
            weights per IS forecast model, i.e.
            source_params = {'ETAS': [a, b, w], ...}.
            Note that the sum of all weights must be 1.0
        :param callback: callback method which will be invoked when the job
            finishes. The callback takes two arguments: job_id (int) and
            success (bool).

        """
        if self.busy:
            raise RuntimeError('OQ jobs cannot run concurrently')
        # prepare hazard input
        self.job_dir = tempfile.mkdtemp(prefix='ramsis-')
        self._logger.debug('Running OQ hazard job from {}'
                           .format(self.job_dir))
        for f in _HAZ_RESOURCES.values():
            shutil.copy(os.path.join(_OQ_RESOURCE_PATH, 'psha', f),
                        self.job_dir)
        source_lt_path = os.path.join(self.job_dir,
                                      _HAZ_RESOURCES['source_lt'])
        utils.inject_src_params(source_params, source_lt_path)
        # run job
        job_def = os.path.join(self.job_dir, _HAZ_RESOURCES['job_def'])
        job_input = {
            'job_def': job_def,
            'job_type': 'hazard'
        }
        self._oq_runner.job_input = job_input
        self.callback = callback
        self.busy = True
        self._oq_thread.start()

    def run_risk_poe(self, psha_job_id, callback):
        """
        Runs an OQ risk job that computes probabilities of exceedance for
        a preconfigured loss range based on the hazard output from a run_hazard
        calculation.

        :param psha_job_id: job id of the run_hazard calculation
        :type psha_job_id: int
        :param callback: callback method which will be invoked when the job
            finishes. The callback takes two arguments: job_id (int) and
            success (bool).

        """
        if self.busy:
            raise RuntimeError('OQ jobs cannot run concurrently')
        # prepare risk input
        self.job_dir = tempfile.mkdtemp(prefix='ramsis-')
        self._logger.debug('Running OQ risk PoE job from {}'
                           .format(self.job_dir))
        for f in _RISK_POE_RESOURCES.values():
            shutil.copy(os.path.join(_OQ_RESOURCE_PATH, 'risk_poe', f),
                        self.job_dir)
        # run job
        job_input = {
            'job_def': os.path.join(self.job_dir,
                                    _RISK_POE_RESOURCES['job_def']),
            'job_type': 'risk',
            'hazard_calculation_id': psha_job_id
        }
        self._oq_runner.job_input = job_input
        self.callback = callback
        self.busy = True
        self._oq_thread.start()

    def _job_complete(self, job_id):
        self.busy = False
        result = {
            'job_id': job_id,
            'success': True
        }
        self._oq_thread.quit()
        self._oq_thread.wait()
        self.callback(result)


controller = _OqController()
