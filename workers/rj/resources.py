from multiprocessing import Process
import json
import requests

from flask import request
from flask_restful import Resource

from model.common import ModelInput
from model.rj import Rj
from settings import settings


class Run(Resource):
    model = None

    def post(self):
        data = json.loads(request.form["data"])
        p = Process(target=self._run, args=(data,))
        p.start()

        response = requests.get(settings["url_next_id"])

    def _run(self, data):
        model_input = ModelInput(None)
        model_input.deserialize(data["model_input"])

        self.model = Rj(**data["parameters"])
        self.model.finished.connect(self._on_model_finished)
        self.model.prepare_run(model_input)
        self.model.run()

    def _on_model_finished(self):
        model_output = self.model.output.serialize()
        data = {"data": json.dumps({"model_output": model_output})}
        requests.post(settings["url_rj"] + '/job1', data)
