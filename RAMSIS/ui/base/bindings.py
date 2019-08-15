# Copyright 2018, ETH Zurich - Swiss Seismological Service SED
"""
Bindings for Qt Widgets

Bindings provide a way to update model values automatically whenever the
respective Qt widgets displaying the value changes.

.. note: Note that unlike traditional bindings, these are uni-directional
because regular python objects don't emit notifications when attributes change.
The :class:`Binding` does provide a :meth:`~Binding.refresh_ui` method to
update the GUI on request.

"""
import abc

from RAMSIS.utils import rgetattr, rsetattr
from RAMSIS.ui.base.controlinterface import control_interface


class Binding(abc.ABC):
    """  The base class for bindings """

    def __init__(self, target, widget, validate=None, post=None):
        """

        :param target: Target model object
        :param QWidget widget: Widget showing the value of the target
        :param validate: Optional validation function accepting the value to
            validate and returning either True or False.
        :param post: Optional function to call after the target value has been
            updated from the widget. This function should accept no parameters.

        """
        self.target = target
        self.widget = widget
        self.validate = validate or (lambda x: True)
        self.post = post
        signal = control_interface(widget).change_signal()
        signal.connect(self.on_widget_changed)

    @property
    def widget_value(self):
        return control_interface(self.widget).get_value()

    @property
    @abc.abstractmethod
    def target_value(self):
        pass

    @target_value.setter
    @abc.abstractmethod
    def target_value(self, value):
        pass

    def refresh_ui(self):
        """ Refresh the UI with the current value from the target """
        control_interface(self.widget).set_value(self.target_value)

    def on_widget_changed(self):
        new_value = self.widget_value
        if self.validate(new_value):
            self.target_value = new_value
            if self.post:
                self.post()
        else:
            self.refresh_ui()


class AttrBinding(Binding):
    """ Binds a widget to an object attribute """

    def __init__(self, target, attr, widget):
        """

        :param str attr: Attribute to bind to
        """
        super().__init__(target, widget)
        self.attr = attr

    @property
    def target_value(self):
        return rgetattr(self.target, self.attr)

    @target_value.setter
    def target_value(self, value):
        rsetattr(self.target, self.attr, value)


class DictBinding(Binding):
    """ Binds a widget to a dict entry """

    def __init__(self, target, key, widget):
        """

        :param str key: Dict key used to set or get value on `target`
        """
        super().__init__(target, widget)
        self.key = key

    @property
    def target_value(self):
        return self.target[self.key]

    @target_value.setter
    def target_value(self, value):
        self.target[self.key] = value


class CallableBinding(Binding):
    """ Binds a widget to a value using a setter and a getter """

    def __init__(self, target, getter, setter, widget):
        """

        :param getter: Getter (must accept a target)
        :param setter: Setter (must accept a target and a value
        """
        super().__init__(target, widget)
        self.getter = getter
        self.setter = setter

    @property
    def target_value(self):
        return self.getter(self.target)

    @target_value.setter
    def target_value(self, value):
        self.setter(self.target, value)
