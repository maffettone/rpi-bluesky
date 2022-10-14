import atexit
import logging
import threading
import time
from typing import Optional

import RPi.GPIO as GPIO
from ophyd import Component, Device, Signal
from ophyd._dispatch import EventDispatcher

module_logger = logging.getLogger(__name__)


class RpiControlLayer:
    """
    Control Layer that is built piecemeal after _caproto_shim to ensure minimal working example.
    This replaces the default in Ophyd and does some Raspberry Pi favors in terms of set up and tear down.
    """

    name = "rpi"

    def __init__(self):
        self.mode = ""
        self.set_mode("BCM")
        self._dispatcher = EventDispatcher(logger=module_logger, context=None)
        atexit.register(self._cleanup)

    def _cleanup(self):
        GPIO.cleanup()
        if self._dispatcher is None:
            return
        if self._dispatcher.is_alive():
            self._dispatcher.stop()
        self._dispatcher = None

    @staticmethod
    def get_pv(pvname: int):
        pass

    @property
    def thread_class(self):
        return threading.Thread

    def get_dispatcher(self):
        return self._dispatcher

    def set_mode(self, mode: str):
        if self.mode:
            raise RuntimeError("GPIO mode can only be set once at the start of a program.")
        self.mode = mode.upper()
        GPIO.setmode(getattr(GPIO, self.mode))


rpi_control_layer = RpiControlLayer()


class RpiSignal(Signal):
    """
    A signal class to handle pins on the RaspberryPi GPIO board.

    There are 2 sensible ways to extend ophyd.Signal:
        1. Override the `put` and `get` methods, making use of ophyd's approach to setting, setting and waiting,
           and reading. That's what we do here.
        2. In the case where your device doesn't have signals that look like a process variable (PV), you
           can go ahead and just override `set` and `read` directly, making sure to understand the use of
           Status (futures) objects in `set`.

    Parameters
    ----------
    pin_number: int
        Pin number for GPIO board
    name: str
        Name of the PV. Defaults to GPIO_pin_{pin_number}
    cl:
        Control layer modeled after the default RPIControlLayer
    parent: OphydObject
        Parent object of the signal
    kwargs:
        Keyword arguments passed to `ophyd.Signal.__init__`
    """

    def __init__(self, pin_number=None, *, name=None, cl=None, parent=None, **kwargs):
        if pin_number is None:
            if parent is None:
                raise AttributeError("Either pin number or parent required for RpiSignal. None given.")
            else:
                pin_number = parent.pin

        GPIO.setup(pin_number, GPIO.OUT)
        name = name or f"GPIO_pin_{pin_number}"
        self.pin = pin_number
        if cl is None:
            cl = rpi_control_layer
        super().__init__(name=name, cl=cl, parent=parent, **kwargs)

    def put(self, value, **kwargs):
        GPIO.output(self.pin, value)
        super().put(value, **kwargs)

    def get(self, **kwargs):
        return GPIO.input(self.pin)


class RpiPWM(Signal):
    """Pulsed width modulation that changes only the duty cylce of the PWM at fixed frequency"""

    dc_bounds = (0, 100)

    def __init__(
        self, pin_number=None, *, frequency=100.0, name=None, cl=None, parent=None, settle_time=None, **kwargs
    ):
        if pin_number is None:
            if parent is None:
                raise AttributeError("Either pin number or parent required for RpiSignal. None given.")
            else:
                pin_number = parent.pin
        self.pin = pin_number
        self.pwm = GPIO.PWM(pin_number, frequency)
        self.pwm.start(0)
        self._current_duty_cycle = 0
        self._settle_time = settle_time or 1.0 / frequency
        name = name or f"PWM_pin_{pin_number}"
        if cl is None:
            cl = rpi_control_layer
        super().__init__(name=name, cl=cl, parent=parent, **kwargs)

    def put(self, value, **kwargs):
        if value < self.dc_bounds[0] or value > self.dc_bounds[1]:
            raise ValueError(f"Duty cycle must be between 0 and 100%. {value} is an invalid set point.")
        self.pwm.ChangeDutyCycle(value)
        self._current_duty_cycle = value
        super().put(value, **kwargs)
        if self._settle_time:
            time.sleep(self._settle_time)

    def get(self, **kwargs):
        return self._current_duty_cycle


class RpiComponent(Component):
    """
    Simple wraper to component that prevents addition of a suffix by positional argument.
    It is not expected that the suffix will ever be needed for Raspberry Pis, but left available as kwarg.
    """

    def __init__(self, cls, **kwargs):
        super().__init__(cls, **kwargs)


class RpiDevice(Device):
    """
    Raspbery Pi GPIO Device. Uses pin number instead of a str suffix.
    Works nicely with RPi Signals and components.
    """

    def __init__(self, pin: Optional[int] = -1, *, name: str, **kwargs):
        self.pin = pin
        super().__init__(pin, name=name, **kwargs)
