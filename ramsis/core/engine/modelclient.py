import json
import requests
import logging

from PyQt4 import QtCore

from core.data.schemas import ForecastSchema, ModelResultSchema


class ModelClient(QtCore.QObject):
    # Signal emitted when model results have been retrieved
    finished = QtCore.pyqtSignal(object)

    def __init__(self, model_info, settings):
        super(ModelClient, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.model_info = model_info
        key = 'worker/%s_url' % self.model_info['model']
        key_database = 'worker/%s_database_url' % self.model_info['model']
        self.url = settings.value(key)
        self.url_database = settings.value(key_database)
        self.poll_interval = 5000  # ms
        self.job_id = None
        self.model = None
        self.model_result = None

    def run(self, forecast):
        """
        Run the model on the remote worker using the settings specified in
        model_input.

        The worker will return a job ID corresponding to the row ID of the
        final results stored in the remote database.

        """
        forecast_schema = ForecastSchema()
        serialized = forecast_schema.dump(forecast).data
        data = {
            "forecast": serialized,
            "parameters": self.model_info["parameters"]
        }

        r = requests.post(self.url, data={"data": json.dumps(data)})
        response = json.loads(r.text)
        try:
            int(response)
            self.job_id = response
        except ValueError:
            self.logger.error("Job ID not received")
            return

        QtCore.QTimer.singleShot(self.poll_interval, self._get_results)

    def _get_results(self):
        """
        Poll the database periodically until the model results have been
        retrieved, then emit the finished signal.

        """
        r = requests.get(self.url).json()
        if r:
            model_result_schema = ModelResultSchema()
            self.model_result = model_result_schema.load(r).data
            self.finished.emit(self)
        else:
            QtCore.QTimer.singleShot(self.poll_interval, self._get_results)

        # headers = {'content-type': 'application/json'}
        # params = {'q': json.dumps({
        #     'filters': [{'name': 'id', 'op': '==', 'val': self.job_id}]
        # })}
        # r = requests.get(self.url_database, params=params, headers=headers)
        # results = json.loads(r.text)
        #
        # # check for results
        # objects = None
        # if "objects" in results:
        #     items = results["objects"][0].items()
        #     result_set = set([v for k, v in items if k != "id"])
        #     if result_set != {None}:
        #         objects = results["objects"]
        #
        # if objects:
        #     row = objects[0]
        #     row["t_run"] = datetime.strptime(row["t_run"], "%Y-%m-%dT%H:%M:%S")
        #
        #     self.model = Model()
        #     model_result = ModelResult(row["rate"], row["b_val"], row["prob"])
        #     model_output = ModelOutput(row["t_run"], row["dt"], self.model)
        #     model_output.failed = row["failed"]
        #     model_output.failure_reason = row["failure_reason"]
        #     model_output.cum_result = model_result
        #     self.model.output = model_output
        #     self.model.title = self.model_info['model']
        #
        #     self.finished.emit(self)
        #
        # else:
        #     seconds = 5
        #     QtCore.QTimer.singleShot(seconds * 1000, self._get_results)
