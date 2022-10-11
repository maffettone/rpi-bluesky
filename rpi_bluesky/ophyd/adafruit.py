from enum import Enum

import board
import numpy as np
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


class AS7341Array(SignalRO):
    def __init__(self, *, parent, name=None, cl=None, **kwargs):
        self._channel_attr = "all_channels"
        name = name if name is not None else self._channel_attr
        if cl is None:
            cl = rpi_control_layer
        super().__init__(name=name, cl=cl, parent=parent, **kwargs)

    def get(self):
        return np.array(getattr(self.parent.sensor, self._channel_attr))

    def describe(self):
        # Because this isn't a simple scalar we need to update the describe dictionary entry
        ret = super().describe()
        ret[f"{self.name}"].update(
            dict(
                dtype="array",
                shape=[8],
            )
        )
        return ret


i2c = board.I2C()


class AS7341Detector(Device):
    """A 10 channel detector that reads in 8 visible channels as an array, and a clear and near_ir channel."""

    sensor = AS7341(i2c)

    visible = RpiComponent(AS7341Array, name="visible", kind="hinted")
    clear = RpiComponent(AS7341Signal, channel="clear", kind="hinted")
    near_ir = RpiComponent(AS7341Signal, channel="near_ir", kind="hinted")
    """
    Each individual channel could be accessed this way. However, the device driver would use re-trigger the read,
    and thus the det.violet would not be guaranteed to match det.visible[0].
    # violet = RpiComponent(AS7341Signal, channel="violet", kind="hinted")
    # indigo = RpiComponent(AS7341Signal, channel="indigo", kind="hinted")
    # blue = RpiComponent(AS7341Signal, channel="blue", kind="hinted")
    # cyan = RpiComponent(AS7341Signal, channel="cyan", kind="hinted")
    # green = RpiComponent(AS7341Signal, channel="green", kind="hinted")
    # yellow = RpiComponent(AS7341Signal, channel="yellow", kind="hinted")
    # orange = RpiComponent(AS7341Signal, channel="orange", kind="hinted")
    # red = RpiComponent(AS7341Signal, channel="red", kind="hinted")
    """
