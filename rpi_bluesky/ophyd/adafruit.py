import threading
from enum import Enum

import board
import numpy as np
from adafruit_as7341 import AS7341
from bluesky.callbacks.core import get_obj_fields
from bluesky.callbacks.mpl_plotting import QtAwareCallback
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


class LiveBars(QtAwareCallback):
    """An effort to make a live plot for this detector that updates on each read."""

    def __init__(self, key, **kwargs):
        super().__init__(use_teleporter=kwargs.pop("use_teleporter", None))
        self.__setup_lock = threading.Lock()
        self.__setup_event = threading.Event()

        def setup():
            # Run this code in start() so that it runs on the correct thread.
            nonlocal key
            import matplotlib.pyplot as plt

            with self.__setup_lock:
                if self.__setup_event.is_set():
                    return
                self.__setup_event.set()
            fig, ax = plt.subplots()
            self.ax = ax

            self.data_key, *others = get_obj_fields([key])
            self.ax.set_xlabel("Wavelength [nm]")
            self.ax.set_ylabel("Intensity")

        self.__setup = setup

    def start(self, doc):
        self.__setup()
        self.new_data = np.zeros(
            8,
        )
        labels = [f"{x.value}" for x in AS7341Enum][:-2]
        self.rects = self.ax.bar(range(8), self.new_data, tick_label=labels)
        super().start(doc)

    def event(self, doc):
        # This try/except block is needed because multiple event
        # streams will be emitted by the RunEngine and not all event
        # streams will have the keys we want.
        try:
            self.new_data = doc["data"][self.data_key]
        except KeyError:
            # wrong event stream, skip it
            return

    def update_plot(self):
        for rect, h in zip(self.rects, self.new_data):
            rect.set_height(h)
        # Rescale and redraw.
        self.ax.relim(visible_only=True)
        self.ax.autoscale_view(tight=True)
        self.ax.figure.canvas.draw_idle()

    def stop(self, doc):
        super().stop(doc)
