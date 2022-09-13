"""
To run this script, the following is needed.
1. Breadboard, and jumper wires
2. 500-1k ohm resistor
3. LED

Connect the ground of the breadboard to pin 9 on the RPi (or any GND pin).
Connect the ground to a row of the breadboard and insert the long pin of the LED in that row.
Connect the short pin and resistor to another row.
Connect the other end of the resistor and another jumper wire to a third row.
Connect the new jumper wire to pin 11 on the RPi.
"""
from rpi_bluesky.ophyd import RpiSignal
from bluesky import RunEngine
import bluesky.plan_stubs as bps
from bluesky.plans import count
from bluesky.callbacks import LiveTable


RE = RunEngine()


def blink(led):
    """blinks 20 times"""
    for i in range(20):
        yield from bps.mv(led, 1)
        yield from count([led])
        yield from bps.sleep(0.5)
        yield from bps.mv(led, 1)
        yield from count([led])
        yield from bps.sleep(0.5)


def main(gpio_pin_num=11):
    led = RpiSignal(gpio_pin_num, name=f"led_at_pin{gpio_pin_num}")
    RE.subscribe(LiveTable([led.name]))
    RE(blink(led))


if __name__ == "__main__":
    main()
