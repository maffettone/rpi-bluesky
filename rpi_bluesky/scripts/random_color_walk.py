"""
Get a RGB LED to do a random color walk.

Kudos to this link, but with Bluesky doing the Threading for you:
https://grantwinney.com/how-to-use-an-rgb-multicolor-led-with-pulse-width-modulation-pwm-on-the-raspberry-pi/

To run this script, the following is needed.
1. Breadboard, and jumper wires
2. 3 220 ohm resistors (sub optimal current, but sensible)
3. White LED

Connect the ground of the breadboard to pin 9 on the RPi.
Connect the ground to a row of the breadboard and insert the long cathode pin of the LED in that row.
Connect the short pin and resistor to another row.
Connect the other end of the resistor and another jumper wire to a third row.
Connect the new jumper wire to pin 11 on the RPi.

"""

import random
import time

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky import RunEngine
from bluesky.callbacks import LiveTable

from rpi_bluesky.ophyd.devices import RGB_LED

RE = RunEngine()


@bpp.run_decorator()
def random_walk(led, timeout=15.0):
    """Choose a channel. Change the intensity by +/- 10. Continue randomly."""
    dets = [x.pwm for x in [led.red, led.green, led.blue]]

    for signal in dets:
        yield from bps.mv(signal, random.random() * 100)

    start_time = time.time()
    while time.time() - start_time < timeout:
        channel = random.choice([led.red, led.green, led.blue])
        previous = yield from bps.rd(channel.pwm)
        next_c = previous + 10 * random.random() * random.choice([-1, 1])
        next_c = min(100, max(0, next_c))
        yield from bps.mv(channel.pwm, next_c)
        yield from bps.trigger_and_read(dets)
        yield from bps.sleep(0.1)


def main():
    led = RGB_LED(9, name="rgb_led")
    led.cl.set_mode("BOARD")  # Required to specify that  we use pin numbers
    RE.subscribe(LiveTable([x.pwm.name for x in [led.red, led.green, led.blue]]))
    RE(random_walk(led))
    return led


if __name__ == "__main__":
    led = main()
