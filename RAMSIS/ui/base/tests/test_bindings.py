# Copyright 2018, ETH Zurich - Swiss Seismological Service SED
"""
Tests for Qt UI bindings

"""

import abc
import unittest
from unittest.mock import patch, Mock

from RAMSIS.ui.base import bindings


def pass_through(arg):
    return arg


ctrlif_mock = Mock()
ctrlif_mock.side_effect = pass_through
patcher = patch('RAMSIS.ui.base.bindings.control_interface', ctrlif_mock)


class Widget:

    class Signal:
        def __init__(self):
            self.slot = None

        def connect(self, slot):
            self.slot = slot

        def emit(self):
            self.slot()

    def __init__(self):
        super().__init__()
        self.value = None
        self.signal = Widget.Signal()

    def change_signal(self):
        return self.signal

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value


@patch('RAMSIS.ui.base.bindings.control_interface')
class TestBinding(abc.ABC):

    @abc.abstractmethod
    def _make_target(self):
        pass

    @abc.abstractmethod
    def _make_binding(self):
        pass

    @abc.abstractmethod
    def _get_target_value(self):
        pass

    @abc.abstractmethod
    def _set_target_value(self, value):
        pass

    def setUp(self):
        patcher.start()
        self.widget = Widget()
        self.target = self._make_target()
        self.binding = self._make_binding()

    def tearDown(self):
        patcher.stop()

    def test_get_widget_value(self, ctrlif_mock):
        ctrlif_mock.side_effect = pass_through
        self.widget.value = 1
        self.assertEqual(self.binding.widget_value, 1)

    def test_get_target_value(self, ctrlif_mock):
        ctrlif_mock.side_effect = pass_through
        self._set_target_value(2)
        self.assertEqual(self.binding.target_value, 2)

    def test_set_target_value(self, ctrlif_mock):
        ctrlif_mock.side_effect = pass_through
        self.binding.target_value = 3
        self.assertEqual(self._get_target_value(), 3)

    def test_refresh_ui(self, ctrlif_mock):
        ctrlif_mock.side_effect = pass_through
        self._set_target_value(4)
        self.binding.refresh_ui()
        self.assertEqual(self.widget.value, 4)

    def test_update(self, ctrlif_mock):
        ctrlif_mock.side_effect = pass_through
        self.widget.value = 5
        self.widget.signal.emit()
        self.assertEqual(self._get_target_value(), 5)

    def test_validation_true(self, ctrlif_mock):
        ctrlif_mock.side_effect = pass_through
        self.binding.validate = lambda v: True
        self.binding.post = Mock()
        self.widget.value = 5
        self.widget.signal.emit()
        self.assertEqual(self._get_target_value(), 5)
        self.binding.post.assert_called_once()

    def test_validation_false(self, ctrlif_mock):
        ctrlif_mock.side_effect = pass_through
        self.binding.validate = lambda v: False
        self.binding.post = Mock()
        self._set_target_value(6)
        self.widget.value = 'invalid'
        self.widget.signal.emit()
        self.assertEqual(self._get_target_value(), 6)
        self.assertEqual(self.widget.value, 6)
        self.binding.post.assert_not_called()


class TestAttrBinding(TestBinding, unittest.TestCase):

    def _make_target(self):
        class Target:
            val = None
        return Target()

    def _make_binding(self, *args):
        return bindings.AttrBinding(self.target, 'val', self.widget)

    def _get_target_value(self):
        return self.target.val

    def _set_target_value(self, value):
        self.target.val = value


class TestDictBinding(TestBinding, unittest.TestCase):

    def _make_target(self):
        return {'val': None}

    def _make_binding(self, *args):
        return bindings.DictBinding(self.target, 'val', self.widget)

    def _get_target_value(self):
        return self.target['val']

    def _set_target_value(self, value):
        self.target['val'] = value


class TestCallableBinding(TestBinding, unittest.TestCase):

    def _make_target(self):
        return {'val': None}

    def _make_binding(self, *args):
        return bindings.CallableBinding(self.target, self._getter,
                                        self._setter, self.widget)

    def _get_target_value(self):
        return self.target['val']

    def _set_target_value(self, value):
        self.target['val'] = value

    def _setter(self, target, value):
        target['val'] = value

    def _getter(self, target):
        return target['val']
