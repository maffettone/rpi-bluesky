"""
Get a RGB LED to do a random color walk.

Kudos to this link, but with Bluesky doing the Threading for you:
https://grantwinney.com/how-to-use-an-rgb-multicolor-led-with-pulse-width-modulation-pwm-on-the-raspberry-pi/

To run this script, the following is needed.
1. Breadboard, and jumper wires
2. 3 220 ohm resistors (sub optimal current, but sensible)
3. White LED

Connect the ground of the breadboard to pin GROUND (e.g 9)  on the RPi.
Connect the ground to a row of the breadboard and insert the long cathode pin of the LED in that row.
Connect the pin GPIO17 on the RPi to a resistor, and the other end of the resistor to the red led pin.
Connect the pin GPIO27 on the RPi to a resistor, and the other end of the resistor to the green led pin.
Connect the pin GPIO22 on the RPi to a resistor, and the other end of the resistor to the blue led pin.
"""

import random
import time

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky import RunEngine
from bluesky.callbacks import LiveTable

from rpi_bluesky.ophyd.adafruit import AS7341Detector, LiveBars
from rpi_bluesky.ophyd.devices import RGB_LED

RE = RunEngine()


@bpp.run_decorator()
def random_walk(led, dets, timeout=30.0):
    """Choose a channel. Change the intensity by +/- 10. Continue randomly."""
    pwms = [x.pwm for x in [led.red, led.green, led.blue]]  # Pulsed width modulators
    dets = dets + pwms

    for signal in pwms:
        yield from bps.mv(signal, random.random() * 100)

    start_time = time.time()
    while time.time() - start_time < timeout:
        channel = random.choice([led.red, led.green, led.blue])
        previous = yield from bps.rd(channel.pwm)
        next_c = previous + 20 * random.random() * random.choice([-1, 1])
        next_c = min(100, max(0, next_c))
        yield from bps.mv(channel.pwm, next_c)
        yield from bps.trigger_and_read(dets)
        # yield from bps.sleep(0.1)


def main():
    led = RGB_LED(name="rgb_led")
    det = AS7341Detector(name="det")
    RE.subscribe(LiveTable([x.pwm.name for x in [led.red, led.green, led.blue]] + [det.near_ir, det.clear]))
    RE.subscribe(LiveBars(det.visible.name))
    RE(random_walk(led, [det]))
    return led


if __name__ == "__main__":
    led = main()
