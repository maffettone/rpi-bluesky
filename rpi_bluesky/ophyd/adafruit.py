from enum import Enum

import board
from adafruit_as7341 import AS7341
from ophyd import Device, SignalRO

from rpi_bluesky.ophyd.base import RpiComponent, rpi_control_layer


class AS7341Enum(Enum):
    VIOLET = 415
    INDIGO = 445
    BLUE = 480
    CYAN = 515
    GREEN = 555
    YELLOW = 590
    ORANGE = 630
    RED = 680
    CLEAR = "clear"
    NEAR_IR = "nir"


class AS7341Signal(SignalRO):
    """
    An Enum and a Read Only Signal. Why? Because this device has a fixed number of sensors channels with
    fixed definition, and they have an order to them. Admittedly, we don't take full advantage of the Enum here
    and it potentially overcomplicates things.
    """

    def __init__(self, channel: str, *, parent, name=None, cl=None, **kwargs):
        self.channel = getattr(AS7341Enum, channel.upper()).value
        self._channel_attr = (
            f"channel_{self.channel}nm" if isinstance(self.channel, int) else f"channel_{self.channel}"
        )
        name = name if name is not None else self._channel_attr
        if cl is None:
            cl = rpi_control_layer
        super().__init__(name=name, cl=cl, parent=parent, **kwargs)

    def get(self):
        return getattr(self.parent.sensor, self._channel_attr)


i2c = board.I2C()


class AS7341Detector(Device):

    sensor = AS7341(i2c)

    # I could loop over the Enum, but it would require a meta class, and that seems a bit much for a tutorial...
    violet = RpiComponent(AS7341Signal, channel="violet", kind="hinted")
    indigo = RpiComponent(AS7341Signal, channel="indigo", kind="hinted")
    blue = RpiComponent(AS7341Signal, channel="blue", kind="hinted")
    cyan = RpiComponent(AS7341Signal, channel="cyan", kind="hinted")
    green = RpiComponent(AS7341Signal, channel="green", kind="hinted")
    yellow = RpiComponent(AS7341Signal, channel="yellow", kind="hinted")
    orange = RpiComponent(AS7341Signal, channel="orange", kind="hinted")
    red = RpiComponent(AS7341Signal, channel="red", kind="hinted")
    clear = RpiComponent(AS7341Signal, channel="clean", kind="hinted")
    near_ir = RpiComponent(AS7341Signal, channel="near_ir", kind="hinted")
