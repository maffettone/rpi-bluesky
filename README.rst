===========
RPi Bluesky
===========

.. image:: https://img.shields.io/pypi/v/rpi-bluesky.svg
        :target: https://pypi.python.org/pypi/rpi-bluesky


Minimum working examples of bluesky using a Raspbery pi and some simple electronics. 

* Free software: 3-clause BSD license
* Documentation: (COMING SOON!) https://maffettone.github.io/rpi-bluesky.

Notes
-----
* create venv with --system-site-packages flag
* Required install of libatlas-base-dev via apt on the RPi (to get numpy)
* Required install of qtbase5-dev via apt on the RPi (for PyQt5)
* sudo apt-get install python3-pyqt5.qtsvg ( Whatever is necessary to get `%matplotlib qt` to work)