from rpi_bluesky.ophyd import RpiSignal, RpiPWM, RpiComponent, RpiDevice


class LED(RpiDevice):
    io = RpiComponent(RpiSignal, name="io")
    pwm = RpiComponent(RpiPWM, name="pwm")
