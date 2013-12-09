# -*- encoding: utf-8 -*-
"""
Short Description

Long Description
    
Copyright (C) 2013, ETH Zurich - Swiss Seismological Service SED

"""

import unittest
from datetime import datetime, timedelta
from eqstats import SeismicRateHistory, SeismicRate


class RateComputationTest(unittest.TestCase):
    """ Tests EQ rates computations """

    def setUp(self):
        """
        Create five events spaced by one hour starting on Nov. 27 2013 at 09:15

        """
        start = datetime(2013, 11, 27, 9, 15)
        dt = timedelta(hours=1)
        self.magnitudes = [4, 5.1, 5, 3.8, 2.6]
        self.times = [start + i*dt for i in range(len(self.magnitudes))]
        self.rate_history = SeismicRateHistory()

    def test_exact_range(self):
        """ Test rate computation for the exact t/M range of the events"""
        t_max = max(self.times)
        dt = (max(self.times) - min(self.times)).total_seconds() / 3600.0

        rates = self.rate_history.compute_and_add(self.magnitudes, self.times,
                                                  [t_max], dt)
        self.assertEqual(rates[0].rate, 1.25)

    def test_one_range(self):
        """ Test rate computation for a larger t_range """
        t_max = datetime(2013, 11, 27, 14)
        dt = (t_max - datetime(2013, 11, 27, 9)).total_seconds() / 3600.0

        rates = self.rate_history.compute_and_add(self.magnitudes, self.times,
                                                  [t_max], dt)
        self.assertEqual(rates[0].rate, 1)

    def test_multiple_bins(self):
        """ Test multiple t bins """
        start = datetime(2013, 11, 27, 9)
        dt = timedelta(hours=3)
        t_range = [start + i * dt for i in range(1, 3)]
        rates = self.rate_history.compute_and_add(self.magnitudes,
                                                  self.times,
                                                  t_range,
                                                  dt.total_seconds() / 3600.0)

        # The first time bin has 1 event
        self.assertEqual(rates[0].rate, 1)
        # The second time bin has 2 events
        self.assertEqual(rates[1].rate, 2.0/3)



if __name__ == '__main__':
    unittest.main()