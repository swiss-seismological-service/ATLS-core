# -*- encoding: utf-8 -*-
"""
A bunch of useful general helpers
    
Copyright (C) 2013, ETH Zurich - Swiss Seismological Service SED

"""

import functools
import cProfile
import pstats
import StringIO
import logging


# note that this decorator ignores **kwargs
def memoize(obj):
    """
    Memoization decorator

    A memoize decorated function is only evaluated on the first call. The result
    is cached and returned without reevaluation on subsequent calls.
    (from https://wiki.python.org/moin/PythonDecoratorLibrary#Memoize)

    """
    cache = obj.cache = {}

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        if args not in cache:
            cache[args] = obj(*args, **kwargs)
        return cache[args]
    return memoizer


class Profiler:
    """
    App performance profiler

    Usage: simple: initialize, start and stop at appropriate locations in the
    code. Cumulative times will be written to the filename given in the
    constructor.

    """
    def __init__(self, file_name=None):
        self.profile = cProfile.Profile()
        self.file_name = file_name

    def start(self):
        self.profile.enable()

    def stop(self):
        self.profile.disable()
        s = StringIO.StringIO()
        sort_by = 'cumulative'
        ps = pstats.Stats(self.profile, stream=s).sort_stats(sort_by)

        if self.file_name is not None:
            ps.dump_stats(self.file_name)
        else:
            ps.print_stats()
            print s.getvalue()


class AtlsLogger (logging.Logger):
    """
    Custom logger that provides an additional log level 'NOTICE' for stuff that

    """
    def __init__(self, name, level=logging.NOTSET):
        super(AtlsLogger, self).__init__(name, level)
        try:
            notice_level = logging.NOTICE
        except:
            raise AttributeError('AtlsLogger expects a NOTICE level to be'
                                 'present in logging.')
        setattr(self, 'notice', lambda message, *args:
                self.log(logging.NOTICE, message, args))