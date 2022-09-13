"""
Make an LED dim in bluesky.

To run this script, the following is needed. (Same setup as blink.py)
1. Breadboard, and jumper wires
2. 500-1k ohm resistor
3. LED

Connect the ground of the breadboard to pin 9 on the RPi (or any GND pin).
Connect the ground to a row of the breadboard and insert the long pin of the LED in that row.
Connect the short pin and resistor to another row.
Connect the other end of the resistor and another jumper wire to a third row.
Connect the new jumper wire to pin 11 on the RPi.
"""
import bluesky.plan_stubs as bps
from bluesky import RunEngine
from bluesky.callbacks import LiveTable
from bluesky.plans import scan

from rpi_bluesky.ophyd.devices import LED

RE = RunEngine()


def dimmer_scan(led):
    """Brightens LED then dims the LED over 50 points with a 1 second break in between"""
    yield from bps.mv(led.io, 1)
    yield from scan([led.io, led.pwm], led.pwm, 0.0, 100.0, 50)
    yield from bps.sleep(1.0)
    yield from scan([led.io, led.pwm], led.pwm, 100.0, 0.0, 50)
    yield from bps.mv(led.io, 0)


def main(gpio_pin_num=11):
    led = LED(gpio_pin_num, name=f"led_at_pin_{gpio_pin_num}")
    RE.subscribe(LiveTable([led.io.name, led.pwm.name]))
    RE(dimmer_scan(led))


if __name__ == "__main__":
    main()
