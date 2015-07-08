# -*- encoding: utf-8 -*-
"""
Short Description

Long Description
    
Copyright (C) 2013, ETH Zurich - Swiss Seismological Service SED

"""

from PyQt4.QtCore import QVariant, Qt
from qgis.core import QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, \
                      QgsPoint, QgsSingleSymbolRendererV2, QgsSymbolV2, \
                      QgsSimpleMarkerSymbolLayerV2


class AtlsDataPointsLayer(QgsVectorLayer):

    def __init__(self, name):
        super(AtlsDataPointsLayer, self).__init__('Point', name, 'memory')


class AtlsLossPoeLayer(AtlsDataPointsLayer):

    def __init__(self, name):
        super(AtlsLossPoeLayer, self).__init__(name)

        pr = self.dataProvider()
        pr.addAttributes([QgsField('name', QVariant.String),
                          QgsField('loss', QVariant.Double)])
        self.updateFields()
        self.rendererV2().symbol().setColor(Qt.red)

    def set_losses(self, losses):
        """
        Set losses to display on the layer

        :param losses: list of dicts containing at least 'name', 'location' (a
            lon, lat tuple), 'loss' and 'poE' (probability of exceedance)

        """
        pr = self.dataProvider()
        pr.deleteFeatures(self.allFeatureIds())

        max_loss = max(loss['loss'] for loss in losses)
        symbol_layer = self.rendererV2().symbol().symbolLayer(0)
        symbol_layer.setDataDefinedProperty('size', '"loss" / {} * 100'
                                            .format(max_loss))

        features = []
        for loss in losses:
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPoint(QgsPoint(*loss['location'])))
            loss_val = loss['loss']
            f.setAttributes([loss['name'], loss_val])
            features.append(f)

        pr.addFeatures(features)
        self.updateExtents()

    def clear(self):
        self.dataProvider().deleteFeatures(self.allFeatureIds())
