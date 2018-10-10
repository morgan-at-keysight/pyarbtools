=====
Usage
=====

To use pyarbtools in a project::

    import pyarbtools


Create a class with the signal generator type and the instrument's IP
address::

    m8190a = pyarbtools.M8910A('192.168.1.12')
    n5182b = pyarbtools.VSG('192.168.1.13')

Supported instruments include:

* :ref:`M8190A` AWG
* :ref:`M8195A` AWG
* :ref:`VSG`
    * E8267D PSG
    * N5182B MXG
    * N5172B EXG
* :ref:`N5193A + N5194A` Vector UXG


===============
Class Structure
===============

Every class is built on a robust socket connection that allows the user
to send SCPI commands/queries, send/receive data using IEEE 488.2
binary block format, check for errors, and gracefully disconnect
from the instrument. Methods were named so that those coming from
using a VISA interface would be familiar with syntax. This
architectural decision was made to provide additional flexibility
for users who need to use specific setup commands not covered by
built-in functions::

    m8190a.write('*RST')
    instID = m8190a.query('*IDN?')
    m8190a.binblockwrite('trace:data 1, 0, ', data)
    m8190a.disconnect()

Each instrument class includes a method to download waveform data to
the signal generator in each supported data format. For example, the
M8190A can accept both real and iq waveforms, so there are two
waveform download methods::

    """Create waveform data here."""
    wfmI, wfmQ = iq_waveform(args)
    wfm = real_waveform(args)

    m8190a.download_wfm(wfm)
    m8190a.download_iq_wfm(wfmI, wfmQ)

These waveform download methods determine if a given waveform meets
minimum length and granularity requirements for the generator being
used and applies appropriate binary formatting to the data. A
descriptive exception is raised if these requirements aren't met by
the waveform.

Each instrument class includes a ``.configure()`` method that should
be called immediately after connecting. It configures several settings
on the signal generator *and sets class attributes* so that the user
knows how the generator is configured and can use those variables in
code without having to send a SCPI query to determine values::

    m8190a.configure(res='wsp', clkSrc='int', fs=7.2e9)
    print(f'Sample rate is {m8190a.fs} samples/sec.')

    recordLength = 1000
    print(f'Waveform play time is {recordLength / m8190a.fs} seconds.')


.. _M8190A:

M8190A
------

When an instance of an instrument is created, pyarbtools connects to
the instrument at the IP address given by the user and sends a few
queries. Each class constructor has a ``reset`` keyword argument that
causes the instrument to perform a default setup prior to running the
rest of the code. It's set to ``False`` by default to prevent unwanted
settings changes.

Several class attributes are set via SCPI queries right off the bat.


``M8190A``.\ **configure**\ (*res*, *clkSrc*, *fs*, *refSrc*, *refFreq*, *out1*, *out2*, *func1*, *func2*, *cf1*, *cf2*)

Sets the basic configuration for M8190A and populates class attributes
accordingly. It should be called any time these settings are changed
(ideally *once* directly after creating the M8190A object).

* ``res``: AWG resolution. Arguments are ``'wpr'``, ``'wsp'`` (default), ``'intx3'``, ``'intx12'``, ``'intx24'``, or ``'intx48'``.
* ``clkSrc``: Sample clock source. Arguments are ``'int'`` (default) or ``'ext'``.
* ``fs``: Sample rate. Argument is a floating point value from 125e6 to 12e9.
* ``refSrc``: Reference clock source. Arguments are ``'axi'`` (default), ``'int'``, ``'ext'``.
* ``refFreq``: Reference clock frequency. Argument is a floating point value from 1e6 to 200e6 in steps of 1e6. Default is 100e6.
* ``out1``, ``out2``: Output signal path for channel 1 and 2 respectively. Arguments are ``'dac'`` (default), ``'dc'``, ``'ac'``.
* ``func1``, ``func2``: Function of channel 1 and 2 respectively. Arguments are ``'arb'`` (default), ``'sts'``, or ``'stc'``.
* ``cf1``, ``cf2``: Carrier frequency of channel 1 and 2 respectively. This setting is only applicable if the digital upconverter is being used (``res`` arguments of ``'intx<#>'``). Arguments are floating point values between 0 and 12e9.


``M8190A``.\ **download_wfm**\ (*wfm*, *ch*)

Defines and downloads a waveform into the lowest available segment slot.

* ``wfm``: NumPy array containing real waveform samples (not IQ).
* ``ch``: Channel to which waveform will be assigned (default is 1).


``M8190A``.\ **download_iq_wfm**\ (*i*, *q*, *ch*)

Defines and downloads a waveform into the lowest available segment slot
while checking that the waveform meets minimum waveform length and
granularity requirements.

* ``i``: NumPy array of values representing the real component of an IQ waveform.
* ``q``: NumPy array of values representing the imaginary component of an IQ waveform.
* ``ch``: Channel to which waveform will be assigned (default is 1).

.. _M8195A:

M8195A
------

``M8195A``.\ **configure**\ (*dacMode*, *fs*, *refSrc*, *refFreq*, *func*)
(self, dacMode='single', fs=64e9, refSrc='axi', refFreq=100e6, func='arb'):

Sets the basic configuration for M8195A and populates class attributes
accordingly. It should be called any time these settings are changed
(ideally *once* directly after creating the M8195A object).

* ``dacMode``: Sets the DAC mode. Arguments are ``'single'`` (default), ``'dual'``, ``'four'``, ``'marker'``, ``'dcd'``, or ``'dcm'``.
* ``clkSrc``: Sample clock source. Arguments are ``'int'`` (default), ``'ext'``, ``'sclk1'``, or ``'sclk2'``.
* ``fs``: Sample rate. Argument is a floating point value from 53.76e9 to 65e9.
* ``refSrc``: Reference clock source. Arguments are ``'axi'`` (default), ``'int'``, ``'ext'``.
* ``refFreq``: Reference clock frequency. Argument is a floating point value from 10e6 to 300e6 in steps of 1e6. Default is 100e6.
* ``func``: Function of channels. Arguments are ``'arb'`` (default), ``'sts'``, or ``'stc'``.


``M8195A``.\ **download_wfm**\ (*wfm*, *ch*)

Defines and downloads a waveform into the lowest available segment slot.

* ``wfm``: NumPy array containing real waveform samples (not IQ).
* ``ch``: Channel to which waveform will be assigned (default is 1).


.. _VSG:

VSG
---

.. _N5193A + N5194A:

N5193A + N5194A
---------------
