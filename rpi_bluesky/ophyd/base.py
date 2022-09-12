import threading

from ophyd import Signal
import RPi.GPIO as GPIO


class RpiControlLayer:
    """
    Control Layer that is only really used to pass along the thread class.
    `get_pv` is required by docstrings, but not actually used.
    """

    def __init__(self):
        """Set up only to use Board pin numbers and not Broadcom SOC"""
        GPIO.cleanup()
        GPIO.setmode(GPIO.BOARD)

    @staticmethod
    def get_pv(pvname: int):
        pass

    @property
    def thread_class(self):
        return threading.Thread


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
