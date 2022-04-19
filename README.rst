=================================================================
PyArbTools: Keysight Signal Generator Control & Waveform Creation
=================================================================

*Current version: 2022.04.1*

Frustrated after looking through hundreds of pages of user manuals to find out how to download a waveform to a signal generator?

Need to test your amplifier or filter with a complex signal but don't want to crack open your digital signal processing books from college?

Tired of troubleshooting VISA connections, conflicts, and incompatibilities?

Can't get a Matlab license or the correct toolbox(es) for your work?

**Try PyArbTools: a fast, free, and flexible way to create waveforms and control Keysight signal generators** *(and VSA software!).*

PyArbTools is a collection of Python classes and functions that provide basic signal creation, instrument configuration, and waveform download capabilities for Keysight signal sources.

It is *loosely* based on Keysight's `IQ Tools <https://www.keysight.com/us/en/lib/software-detail/computer-software/keysight-iqtools.html>`_, a Matlab-based toolkit that accomplishes similar things.
PyArbTools was built to satisfy the needs of signal generator users who can't/don't want to use Matlab and to improve code readability and documentation.

**Features**

* Supported signal generators:
    * M9384B VXG vector signal generator
    * N5182B MXG, N5172B EXG, and E8267D PSG vector signal generators
    * M8190A, M8195A, and M8196A arbitrary waveform generators
    * N5193A and N5194A UXG agile waveform generators.
* Connect to and configure instruments, download waveforms, control playback, and load or stream PDWs (for UXG), all using easy-to-use functions rather than a list of SCPI commands.
* Create sequences on the M8190A.
* Automate waveform analysis using Keysight's 89600 VSA software.
* For custom applications, communicate with instruments using SCPI commands.
* All instrument control uses socket communication, no VISA required.

`DOCUMENTATION <https://pyarbtools.readthedocs.io/en/master>`_

Take a look at `pyarbtools/examples.py <https://github.com/morgan-at-keysight/pyarbtools/blob/master/examples.py>`_ for sample code.

*PyArbTools was written for Python and is not currently compatible with legacy Python 2.x*