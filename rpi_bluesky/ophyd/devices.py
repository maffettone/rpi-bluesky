from rpi_bluesky.ophyd import RpiComponent, RpiDevice, RpiPWM, RpiSignal


class LED(RpiDevice):
    io = RpiComponent(RpiSignal, name="io")
    pwm = RpiComponent(RpiPWM, name="pwm")


class RGB_LED(RpiDevice):
    """Notice how this device requires hard coding of the channels"""

    red = RpiComponent(LED, pin=11, name="red")
    green = RpiComponent(LED, pin=13, name="green")
    blue = RpiComponent(LED, pin=15, name="blue")
