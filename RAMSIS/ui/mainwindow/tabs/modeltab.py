# Copyright 2018, ETH Zurich - Swiss Seismological Service SED
"""
Status tab presenting facilities.
"""

import numpy as np
from .tabs import TabPresenter


class ModelTabPresenter(TabPresenter):
    """
    Handles the Induced Seismicity tabs content

    """
    def __init__(self, ui):
        """
        :param ui: reference to the Qt UI
        :type ui: Ui_ForecastsWindow
        """

        super(ModelTabPresenter, self).__init__(ui)
        self.ui.modelSelectorComboBox.currentIndexChanged.connect(
            self.action_model_selection_changed)

    def refresh(self):
        """
        Refresh everything

        """
        # TODO LH: the rabbit hole is now much deeper. adapt.
        # fc_result = self.scenario.forecast_result
        # self._update_models_list(fc_result)
        # model_result = self._get_selected_model_result(fc_result)
        # self._present_model_result(model_result)

    def _present_model_result(self, model_result):
        """
        Update the forecast results shown in the window with the ISModelResult
        passed in to the function.

        :param model_result: ISModelResult object to display or None to clear
        :type model_result: ISModelResult or None

        """

        self._show_is_results(model_result)

        # TODO
        # self._show_is_score(model_result)
        # self._show_spatial_is(model_result)

    def _show_is_results(self, model_result):
        """
        Update the forecast result labels

        :param model_result: latest model result
        :type model_result: ISModelResult or None

        """
        if model_result is None:
            self.ui.predRateLabel.setText('-')
            self.ui.bValLabel.setText('-')
        else:
            try:
                self.ui.predRateLabel.setText('{:.3f}'.format(
                    model_result.rate_prediction.rate))
                self.ui.bValLabel.setText('{:.3f}'.format(
                    model_result.rate_prediction.b_val))
            except AttributeError:
                self.ui.predRateLabel.setText('No Results')
                self.ui.bValLabel.setText('No Results')

    def _show_is_score(self, model_result):
        """
        Update the model score labels (time and LL of latest rating)

        :param model_result: model result containing the latest score or None
        :type model_result: ISModelResult or None

        """
        try:
            score = model_result.rate_prediction.score
        except AttributeError:
            score = None
        if model_result is None or score is None:
            ll = 'N/A'
            t = ''
        else:
            ll = '{:.1f}'.format(score.LL)
            fc_time = model_result.forecast_result.forecast.forecast_time \
                .ctime()
            t = '@ {}'.format(fc_time)
        self.ui.scoreLabel.setText(ll)
        self.ui.scoreTimeLabel.setText(t)

    def _show_spatial_is(self, model_result):
        """
        Show the latest spatial results (if available) for the model output
        passed into the method.

        :param model_result: model result or None
        :type model_result: ISModelResult or None

        """
        mr = model_result
        try:
            vol_rates = mr.get_rates()
        except AttributeError:
            vol_rates = None
        if mr is None or mr.failed or not vol_rates:
            self.ui.voxelPlot.set_voxel_data(None)
            self.logger.debug('No spatial results available to plot')
        else:
            self.logger.debug('Max voxel rate is {:.1f}'.
                              format(np.amax(vol_rates)))
            self.ui.voxelPlot.set_voxel_data(vol_rates)

    # Helpers

    def _get_selected_model_result(self, fc_result):
        if fc_result is None or len(fc_result.model_results) == 0:
            return None
        idx = self.ui.modelSelectorComboBox.currentIndex()
        model_id = self.ui.modelSelectorComboBox.itemData(idx)
        model_result = fc_result.model_results[model_id]
        return model_result

    def _update_models_list(self, fc_result):
        """
        Update the list of models from the forecast results.

        :param fc_result: forecast result or None
        :type fc_result: ForecastResult or None

        """
        self.ui.modelSelectorComboBox.clear()
        if fc_result is None:
            return
        self.ui.modelSelectorComboBox.currentIndexChanged.disconnect(
            self.action_model_selection_changed)
        models = fc_result.scenario.project.settings['forecast_models']
        for i, m in enumerate(fc_result.model_results.values()):
            title = models[m.model_id]['title']
            self.ui.modelSelectorComboBox.insertItem(i, title, m.model_id)
        self.ui.modelSelectorComboBox.currentIndexChanged.connect(
            self.action_model_selection_changed)

    # Button Actions

    def action_model_selection_changed(self, _):
        fc_result = self.scenario.forecast_result
        model_result = self._get_selected_model_result(fc_result)
        self._present_model_result(model_result)
