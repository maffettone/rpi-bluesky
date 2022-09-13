import threading
import atexit
import logging

from ophyd import Signal
from ophyd._dispatch import EventDispatcher
import RPi.GPIO as GPIO

module_logger = logging.getLogger(__name__)


class RpiControlLayer:
    """
    Control Layer that is built piecemeal after _caproto_shim to ensure minimal working example.
    Maffettone has no idea what he's doing...
    """

    name = "rpi"

    def __init__(self):
        """Set up only to use Board pin numbers and not Broadcom SOC"""
        GPIO.setmode(GPIO.BOARD)
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


rpi_control_layer = RpiControlLayer()


class RpiSignal(Signal):
    def __init__(self, pin_number, *, name=None, cl=None, **kwargs):
        GPIO.setup(pin_number, GPIO.OUT)
        name = name or f"GPIO_pin_{pin_number}"
        self.pin = pin_number
        if cl is None:
            cl = rpi_control_layer
        super().__init__(name=name, cl=cl, **kwargs)

    def put(self, value, **kwargs):
        self._validate_put(value)
        GPIO.output(self.pin, value)
        super().put(value, **kwargs)

    def get(self, **kwargs):
        return GPIO.input(self.pin)

    @staticmethod
    def _validate_put(val):
        if val not in {False, True, 1, 0, 1.0, 0.0, GPIO.LOW, GPIO.HIGH}:
            raise ValueError(f"{val} is not a valid value for setting a GPIO pin.")
