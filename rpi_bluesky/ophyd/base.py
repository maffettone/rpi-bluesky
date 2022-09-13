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
        GPIO.output(self.pin, value)
        super().put(value, **kwargs)

    def get(self, **kwargs):
        return GPIO.input(self.pin)


class RpiPWM(Signal):
    """Pulsed width modulation that changes only the duty cylce of the PWM at fixed frequency"""

    dc_bounds = (0, 100)

    def __init__(self, pin_number, *, frequency=100.0, name=None, cl=None, **kwargs):
        self.pin = pin_number
        self.pwm = GPIO.PWM(pin_number, frequency)
        self.pwm.start(0)
        self._current_duty_cycle = 0
        name = name or f"PWM_pin_{pin_number}"
        if cl is None:
            cl = rpi_control_layer
        super().__init__(name=name, cl=cl, **kwargs)

    def put(self, value, **kwargs):
        if value < self.dc_bounds[0] or value > self.dc_bounds[1]:
            raise ValueError(f"Duty cycle must be between 0 and 100%. {value} is an invalid set point.")
        self.pwm.ChangeDutyCycle(value)
        self._current_duty_cycle = value

    def get(self, **kwargs):
        return self._current_duty_cycle
