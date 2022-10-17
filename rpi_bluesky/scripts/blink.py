"""
Make an LED blink in bluesky using an extensive plan, or a modification of a prepackaged scan.

To run this script, the following is needed.
1. Breadboard, and jumper wires
2. 500-1k ohm resistor
3. LED

Connect the ground of the breadboard to pin GROUND on the RPi.
Connect the ground to a row of the breadboard and insert the long pin of the LED in that row.
Connect the short pin and resistor to another row.
Connect the other end of the resistor and another jumper wire to a third row.
Connect the new jumper wire to pin GPIO17 on the RPi.
"""
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky import RunEngine
from bluesky.callbacks import LiveTable
from bluesky.plans import list_scan

from rpi_bluesky.ophyd import RpiSignal

RE = RunEngine()


@bpp.run_decorator()
def blink(led):
    """blinks 10 times"""
    for i in range(10):
        yield from bps.mv(led, 1)
        yield from bps.trigger_and_read([led])
        yield from bps.sleep(0.5)
        yield from bps.mv(led, 0)
        yield from bps.trigger_and_read([led])
        yield from bps.sleep(0.5)


def blink_scan(led):
    """blinks 10 times, but in a single run"""

    def per_step(detectors, motor, step):
        yield from bps.one_1d_step(detectors, motor, step)
        yield from bps.sleep(0.5)

    yield from list_scan([led], led, [0 if i % 2 == 0 else 1 for i in range(20)], per_step=per_step)


def main(gpio_pin_num=17):
    led = RpiSignal(gpio_pin_num, name=f"led_at_GPIO{gpio_pin_num}")
    RE.subscribe(LiveTable([led.name]))
    RE(blink(led))
    RE(blink_scan(led))
    RE(bps.mv(led, 0))


if __name__ == "__main__":
    main()
