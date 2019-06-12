# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Utilities for SFM-Worker data import/export.
"""

import base64
import functools
import json

from marshmallow import Schema, fields, pre_dump, post_dump

from RAMSIS.io.seismics import QuakeMLCatalogSerializer
from RAMSIS.io.hydraulics import HYDWSBoreholeHydraulicsSerializer
from RAMSIS.io.utils import SerializerBase, IOBase, _IOError


class SFMWIOError(_IOError):
    """Base SFMW de-/serialization error ({})."""

# TODO(damb): Implement a solution based on hydraulics


class _SchemaBase(Schema):
    """
    Schema base class.
    """
    @classmethod
    def _clear_missing(cls, data):
        retval = data.copy()
        for key in filter(lambda key: data[key] in (None, {}, []), data):
            del retval[key]
        return retval


class _SeismicCatalogSchema(_SchemaBase):
    """
    Schema representation of a seismic catalog.
    """
    # XXX(damb): Use a string in favor of bytes since bytes cannot be
    # serialized into JSON
    quakeml = fields.String(required=True)

    @pre_dump
    def make_catalog(self, data):
        """
        Convert an instance of
        :py:class:`ramsis.datamodel.seismics.SeismicCatalog` into its `QuakeML
        <https://quake.ethz.ch/quakeml/>`_ representation.
        """
        if 'quakeml' in data:
            serializer = QuakeMLCatalogSerializer()

            try:
                data['quakeml'] = serializer.dumps(data['quakeml'])
            except AttributeError:
                pass

        return data

    @post_dump
    def b64encode(self, data):
        """
        Encode the catalog using base64 encoding.
        """
        if 'quakeml' in data:
            data['quakeml'] = base64.b64encode(
                data['quakeml'].encode('utf8')).decode('utf8')

        return data


class _ReservoirSchema(_SchemaBase):
    """
    Schema representation of a reservoir to be forecasted.
    """
    # XXX(damb): WKT/WKB
    geom = fields.String()

    # TODO(damb): Attributes to be verified.
    event_rate = fields.Float()
    b_value = fields.Float()
    std_event_rate = fields.Float()

    # XXX(damb): Currently no sub_geometries are supported.
    # sub_geometries = fields.Nested('self', many=True)


class _ScenarioSchema(_SchemaBase):
    """
    Schema representation for a scenario to be forecasted.
    """
    # XXX(damb): Borehole scenario for both the related geometry and the
    # injection plan.
    well = fields.Dict(keys=fields.Str())

    @pre_dump
    def serialize_well(self, data):
        if 'well' in data:
            serializer = HYDWSBoreholeHydraulicsSerializer(
                plan=True,
                proj=self.context.get('proj'),
                transform_callback=self.context.get('transform_callback'))

            # XXX(damb): This is not a nice solution. Something like
            # marshmallow's dump method would be required to avoid dumping to a
            # string firstly just to load the data afterwards, again.
            data['well'] = json.loads(serializer.dumps(data['well']))

        return data


class _SFMWorkerIMessageSchema(_SchemaBase):
    """
    Schema implementation for serializing input messages for seismicity
    forecast model worker implementations.

    .. note::

        With the current protocol version only a single well is supported.
    """
    seismic_catalog = fields.Nested(_SeismicCatalogSchema)
    # XXX(damb): Implicit definition of an injection well in order to allow
    # serialization by means of the appropriate RT-RAMSIS borehole serializer.
    # Note, that a well comes along with its hydraulics.
    well = fields.Dict(keys=fields.Str())
    scenario = fields.Nested(_ScenarioSchema)
    reservoir = fields.Nested(_ReservoirSchema)
    # XXX(damb): model_parameters are optional
    model_parameters = fields.Dict(keys=fields.Str())

    @pre_dump
    def serialize_well(self, data):
        if 'well' in data:
            serializer = HYDWSBoreholeHydraulicsSerializer(
                plan=False,
                proj=self.context.get('proj'),
                transform_callback=self.context.get('transform_callback'))

            # XXX(damb): This is not a nice solution. Something like
            # marshmallow's dump method would be required to avoid dumping to a
            # string firstly just to load the data afterwards, again.
            data['well'] = json.loads(serializer.dumps(data['well']))

        return data

    @post_dump
    def skip_missing(self, data):
        return self._clear_missing(data)


class SFMWorkerIMessageSerializer(SerializerBase, IOBase):
    """
    Serializes borehole and hydraulics data from the RT-RAMSIS data model.
    """

    SRS_EPSG = 4326

    def __init__(self, **kwargs):
        """
        :param str proj: Spatial reference system in Proj4 notation
            representing the local coordinate system
        :param transform_callback: Function reference for transforming data
            into local coordinate system
        """
        super().__init__(**kwargs)

        self._proj = kwargs.get('proj')
        if not self._proj:
            raise SFMWIOError("Missing SRS (PROJ4) projection.")

    def _serialize(self, data):
        """
        Serializes a SFM-Worker payload from the ORM into JSON.
        """
        crs_transform = self._transform_callback or self._transform

        ctx = {
            'proj': self._proj,
            'transform_callback': functools.partial(
                crs_transform, source_proj=self._proj,
                target_proj=self.SRS_EPSG)}

        return _SFMWorkerIMessageSchema(context=ctx).dumps(data)


IOBase.register(SFMWorkerIMessageSerializer)
SerializerBase.register(SFMWorkerIMessageSerializer)
