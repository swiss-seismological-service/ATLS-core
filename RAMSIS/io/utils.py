# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
General purpose IO utilities.
"""

import abc
import io
import logging

import requests

from ramsis.utils.error import Error


# NOTE(damb): RequestError instances carry the response, too.
class RequestsError(requests.exceptions.RequestException, Error):
    """Base request error ({})."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class _IOError(Error):
    """Base IO error ({})."""


class InvalidProj4(_IOError):
    """Invalid Proj4 projection specified: {}"""


# -----------------------------------------------------------------------------
class IOBase(abc.ABC):
    """
    Abstract IO base class
    """
    LOGGER = 'ramsis.io.io'

    def __init__(self):
        self.logger = logging.getLogger(self.LOGGER)

    @abc.abstractmethod
    def __iter__(self):
        while False:
            yield None


# -----------------------------------------------------------------------------
class ResourceLoader(abc.ABC):
    """
    Abstract resource loader base class. Resource loaders build an abstraction
    layer to pretend file-like objects.
    """

    @abc.abstractmethod
    def _load(self):
        """
        :returns: File-like objects
        """
        return io.BytesIO()

    def __call__(self):
        return self._load()


class FileLikeResourceLoader(ResourceLoader):
    """
    General purpose resource loader adapting the interface of any file-like
    object.
    """

    def __init__(self, file_like_obj):
        """
        :param file_like_obj: File-like object to be wrapped
        """
        self._file_like = file_like_obj

    def _load(self):
        return self._file_like


class HTTPGETResourceLoader(ResourceLoader):
    """
    Resource loader implementing loading data from an URL using the HTTP
    **GET** request method.
    """

    def __init__(self, url, params={}, timeout=None):
        self._url = url
        self._params = params
        self._timeout = timeout

    def _load(self):
        try:
            r = requests.get(self._url,
                             params=self._params,
                             timeout=self._timeout)

        except RequestsError as err:
            # XXX(damb): Make sure that an instance of ramsis.utils.error.Error
            # can be caught
            raise err

        return io.BytesIO(r.content)


class HTTPGETStreamResourceLoader(HTTPGETResourceLoader):
    """
    Resource loader implementing streamed loading from an URL using the HTTP
    **GET** request method.
    """

    def _load(self):
        try:
            r = requests.get(self._url,
                             params=self._params,
                             timeout=self._timeout,
                             stream=True)
            r.raw.decode_content = True
        except RequestsError as err:
            # XXX(damb): Make sure that an instance of ramsis.utils.error.Error
            # can be caught
            raise err

        return r.raw


ResourceLoader.register(FileLikeResourceLoader)
ResourceLoader.register(HTTPGETResourceLoader)
ResourceLoader.register(HTTPGETStreamResourceLoader)
