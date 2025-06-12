=================================================================
PyArbTools: Keysight Signal Generator Control & Waveform Creation
=================================================================


*Current version: 2025.06.1*


Frustrated after looking through hundreds of pages of user manuals to find out how to download a waveform to a signal generator?

Need to test your amplifier or filter with a complex signal but don't want to crack open your digital signal processing books from college?

Tired of troubleshooting VISA connections, conflicts, and incompatibilities?

Can't get a Matlab license or the correct toolbox(es) for your work?

**Try PyArbTools: a fast, free, and flexible way to create waveforms and control Keysight signal generators.**

PyArbTools is a collection of Python classes and functions that provide basic signal creation, instrument configuration, and waveform download capabilities for Keysight signal sources.

It is *loosely* based on Keysight's `IQ Tools <https://www.keysight.com/us/en/lib/software-detail/computer-software/keysight-iqtools.html>`_, a Matlab-based toolkit that accomplishes similar things.
PyArbTools was built to satisfy the needs of signal generator users who can't/don't want to use Matlab and to improve code readability and documentation.

**Features**

* **New in 2023.06.1:** Choose between direct socket communication and PyVISA for all instruments.
* Supports the following instruments:
    * M8190A, M8195A, and M8196A arbitrary waveform generators
    * N5182B MXG, N5172B EXG, E8267D PSG vector signal generators
    * M9384B and M9484C VXG vector signal generators
    * N5186A MXG vector signal generator
* Connect to and configure instruments, download waveforms, and control playback, all using easy-to-use functions rather than a list of SCPI commands.
* Create sequences on the M8190A.
* Calibrate waveforms using Keysight's 89600 VSA software.
* For custom applications, communicate with instruments using SCPI commands.

`DOCUMENTATION <https://pyarbtools.readthedocs.io/en/latest>`_

Take a look at `pyarbtools/examples.py <https://github.com/morgan-at-keysight/pyarbtools/blob/master/examples.py>`_ for sample code.

*PyArbTools was written for Python and is not currently compatible with legacy Python 2.x*

License: GPL 3
