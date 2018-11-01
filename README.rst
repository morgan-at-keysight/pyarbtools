================================================
pyarbtools: Keysight Signal Generator Control
================================================

License: GPL 3

`DOCUMENTATION <https://pyarbtools.readthedocs.io/en/master/index.html>`_

Take a look at `pyarbtools/examples.py <https://github.com/morgan-at-keysight/pyarbtools/blob/master/pyarbtools/examples.py>`_ for sample code.

pyarbtools is a collection of Python classes and functions that provide basic signal creation, instrument configuration, and waveform download capabilities for Keysight signal sources.

It is loosely based on Keysight's `IQ Tools <https://www.keysight.com/main/techSupport.jspx?cc=US&lc=eng&nid=-33319.972199&pid=1969138&pageMode=DS>`_, a Matlab-based toolkit that accomplishes similar things.
pyarbtools was built to satisfy the needs of signal generator users who can't/don't want to use Matlab and to improve code readability and documentation.

pyarbtools currently uses Python's socket module under the hood to communicate with signal generators. This is sufficient for *most* situations, although there are certain instruments that do not support socket communication.

*pyarbtools was written for Python and is not currently compatible with legacy Python 2.*
