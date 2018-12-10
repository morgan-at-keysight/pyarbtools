================================================
pyarbtools: Keysight Signal Generator Control
================================================

License: GPL 3

`DOCUMENTATION <https://pyarbtools.readthedocs.io/en/master/index.html>`_

Take a look at `pyarbtools/examples.py <https://github.com/morgan-at-keysight/pyarbtools/blob/master/pyarbtools/examples.py>`_ for sample code.

pyarbtools is a collection of Python classes and functions that provide basic signal creation, instrument configuration, and waveform download capabilities for Keysight signal sources.

It is loosely based on Keysight's `IQ Tools <https://www.keysight.com/main/techSupport.jspx?cc=US&lc=eng&nid=-33319.972199&pid=1969138&pageMode=DS>`_, a Matlab-based toolkit that accomplishes similar things.
pyarbtools was built to satisfy the needs of signal generator users who can't/don't want to use Matlab and to improve code readability and documentation.

**Features**

* Supports M8190A and M8195A arbitrary waveform generators, N5182B MXG/N5172B EXG/E8267D PSG vector signal generators, and N5193A + N5194A UXG agile waveform generator pair.
* Connect to and configure instruments, download IQ waveforms, control playback, and load or stream PDWs (for UXG), all using individual functions rather than a list of SCPI commands.
* Calibrate waveforms with digital predistortion using Keysight's 89600 VSA software.
* For custom use cases, communicate with instruments using SCPI commands.
* All instrument control uses raw socket protocol, no VISA required.


*pyarbtools was written for Python and is not currently compatible with legacy Python 2.x*
