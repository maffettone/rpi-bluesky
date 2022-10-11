import time

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky import RunEngine
from bluesky.callbacks import LiveTable

from rpi_bluesky.ophyd.adafruit import AS7341Detector

RE = RunEngine()


@bpp.run_decorator()
def read_and_pause(dets, pause=0.5, timeout=15.0):
    start_time = time.time()
    while time.time() - start_time < timeout:
        yield from bps.trigger_and_read(dets)
        yield from bps.sleep(pause)


def main():
    vis_det = AS7341Detector(name="vis_det")
    dets = [vis_det]
    RE.subscribe(LiveTable([vis_det.near_ir, vis_det.clear]))
    RE(read_and_pause(dets))
    return vis_det


if __name__ == "__main__":
    det = main()
