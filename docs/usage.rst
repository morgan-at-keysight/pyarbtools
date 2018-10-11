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



Class Structure
---------------

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


When an instance of an instrument is created, pyarbtools connects to
the instrument at the IP address given by the user and sends a few
queries. Each class constructor has a ``reset`` keyword argument that
causes the instrument to perform a default setup prior to running the
rest of the code. It's set to ``False`` by default to prevent unwanted
settings changes.

Several class attributes are set via SCPI queries right off the bat.

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

**M8190A**
----------

``M8190A``.\ **configure**\ (*res*, *clkSrc*, *fs*, *refSrc*, *refFreq*, *out1*, *out2*, *func1*, *func2*, *cf1*, *cf2*)
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Sets the basic configuration for the M8190A and populates class
attributes accordingly. It should be called any time these settings are
changed (ideally *once* directly after creating the M8190A object).

Arguments
"""""""""
* ``res``: AWG resolution. Arguments are ``'wpr'``, ``'wsp'`` (default), ``'intx3'``, ``'intx12'``, ``'intx24'``, or ``'intx48'``.
* ``clkSrc``: Sample clock source. Arguments are ``'int'`` (default) or ``'ext'``.
* ``fs``: Sample rate. Argument is a floating point value from ``125e6`` to ``12e9``.
* ``refSrc``: Reference clock source. Arguments are ``'axi'`` (default), ``'int'``, ``'ext'``.
* ``refFreq``: Reference clock frequency. Argument is a floating point value from ``1e6`` to ``200e6`` in steps of ``1e6``. Default is ``100e6``.
* ``out1``, ``out2``: Output signal path for channel 1 and 2 respectively. Arguments are ``'dac'`` (default), ``'dc'``, ``'ac'``.
* ``func1``, ``func2``: Function of channel 1 and 2 respectively. Arguments are ``'arb'`` (default), ``'sts'``, or ``'stc'``.
* ``cf1``, ``cf2``: Carrier frequency of channel 1 and 2 respectively. This setting is only applicable if the digital upconverter is being used (``res`` arguments of ``'intx<#>'``). Arguments are floating point values between ``0`` and ``12e9``.


``M8190A``.\ **download_wfm**\ (*wfm*, *ch*)
""""""""""""""""""""""""""""""""""""""""""""

Defines and downloads a waveform into the lowest available segment slot.

Arguments
"""""""""
* ``wfm``: NumPy array containing real waveform samples (not IQ).
* ``ch``: Channel to which waveform will be assigned. Arguments are ``1`` (default) or ``2``.


``M8190A``.\ **download_iq_wfm**\ (*i*, *q*, *ch*)
""""""""""""""""""""""""""""""""""""""""""""""""""

Defines and downloads a waveform into the lowest available segment slot
while checking that the waveform meets minimum waveform length and
granularity requirements.

Arguments
"""""""""
* ``i``: NumPy array of values representing the real component of an IQ waveform.
* ``q``: NumPy array of values representing the imaginary component of an IQ waveform.
* ``ch``: Channel to which waveform will be assigned. Arguments are ``1`` (default) or ``2``.

.. _M8195A:

**M8195A**
----------

``M8195A``.\ **configure**\ (*dacMode*, *fs*, *refSrc*, *refFreq*, *func*)
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Sets the basic configuration for the M8195A and populates class
attributes accordingly. It should be called any time these settings are
changed (ideally *once* directly after creating the M8195A object).

Arguments
"""""""""
* ``dacMode``: Sets the DAC mode. Arguments are ``'single'`` (default), ``'dual'``, ``'four'``, ``'marker'``, ``'dcd'``, or ``'dcm'``.
* ``clkSrc``: Sample clock source. Arguments are ``'int'`` (default), ``'ext'``, ``'sclk1'``, or ``'sclk2'``.
* ``fs``: Sample rate. Argument is a floating point value from ``53.76e9`` to ``65e9``.
* ``refSrc``: Reference clock source. Arguments are ``'axi'`` (default), ``'int'``, ``'ext'``.
* ``refFreq``: Reference clock frequency. Argument is a floating point value from ``10e6`` to ``300e6`` in steps of ``1e6``. Default is ``100e6``.
* ``func``: Function of channels. Arguments are ``'arb'`` (default), ``'sts'``, or ``'stc'``.


``M8195A``.\ **download_wfm**\ (*wfm*, *ch*)
""""""""""""""""""""""""""""""""""""""""""""

Defines and downloads a waveform into the lowest available segment slot.

Arguments
"""""""""
* ``wfm``: NumPy array containing real waveform samples (not IQ).
* ``ch``: Channel to which waveform will be assigned (default is 1).


.. _VSG:

**VSG**
-------

``VSG``.\ **configure**\ (*rfState*, *modState*, *cf*, *amp*, *iqScale*, *refSrc*, *refFreq*, *fs*)
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Sets the basic configuration for M8195A and populates class attributes
accordingly. It should be called any time these settings are changed
(ideally *once* directly after creating the UXG object).

Arguments
"""""""""
* ``rfState``: Turns the RF output state on or off. Arguments are ``0``/``'off'`` (default) or ``1``/``'on'``.
* ``modState``: Turns the modulation state on or off. Arguments are ``0``/``'off'`` (default) or ``1``/``'on'``.
* ``cf``: Sets the output carrier frequency. Argument is a floating point value whose range is instrument dependent. Default is ``1e9``.
    * EXG/MXG ``9e3`` to ``6e9``
    * PSG ``100e3`` to ``44e9``
* ``amp``: Sets the output power. Argument is a floating point value whose range is instrument dependent. Default is ``-130``.
    * EXG/MXG ``-144`` to ``+26``
    * PSG ``-130`` to ``+21``
* ``iqScale``: Sets the IQ scale factor. Argument is an integer from ``1`` to ``100``. Default is ``70``.
* ``refSrc``: Reference clock source. Arguments are ``'int'`` (default), or ``'ext'``.
* ``refFreq``: Reference clock frequency. Argument is a floating point value from ``1e6`` to ``50e6``. Default is ``10e6``.
* ``fs``: Sample rate. Argument is a floating point whose range is instrument dependent.
    * EXG/MXG ``1e3`` to ``200e6``
    * PSG ``1`` to ``100e6``


``VSG``.\ **download_iq_wfm**\ (*name*, *i*, *q*)
"""""""""""""""""""""""""""""""""""""""""""""""""

Defines and downloads a waveform into WFM1: memory directory and checks
that the waveform meets minimum waveform length and granularity
requirements.

Arguments
"""""""""
* ``name``: The waveform name. Argument is a string.
* ``i``: NumPy array of values representing the real component of an IQ waveform.
* ``q``: NumPy array of values representing the imaginary component of an IQ waveform.

.. _N5193A + N5194A:

**N5193A + N5194A**
-------------------

``UXG``.\ **configure**\ (*rfState*, *modState*, *cf*, *amp*, *iqScale*, *refSrc*, *refFreq*, *fs*)
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Sets the basic configuration for M8195A and populates class attributes
accordingly. It should be called any time these settings are changed
(ideally *once* directly after creating the M8195A object).

Arguments
"""""""""
* ``rfState``: Turns the RF output state on or off. Arguments are ``0``/``'off'`` (default) or ``1``/``'on'``.
* ``modState``: Turns the modulation state on or off. Arguments are ``0``/``'off'`` (default) or ``1``/``'on'``.
* ``cf``: Sets the output carrier frequency. Argument is a floating point value from ``50e6`` to ``20e9``. Default is ``1e9``.
* ``amp``: Sets the output power. Argument is a floating point value from ``-120`` to ``+3``. Default is ``-120``.
* ``iqScale``: Sets the IQ scale factor. Argument is an integer from ``1`` to ``100``. Default is ``70``.
* ``refSrc``: Reference clock source. Arguments are ``'int'`` (default), or ``'ext'``.
* ``refFreq``: Reference clock frequency. Argument is fixed at ``10e6``. This argument will be removed in a future release.
* ``fs``: Sample rate. This quantity is fixed based on the instrument's mode (either ``250e6`` or ``2e9``). This argument will be removed in a future release.


``UXG``.\ **download_iq_wfm**\ (*name*, *i*, *q*, *assign*)
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Defines and downloads a waveform into WFM1: memory directory and checks
that the waveform meets minimum waveform length and granularity
requirements. Optionally assigns waveform to active arb memory.

Arguments
"""""""""
* ``name``: The waveform name. Argument is a string.
* ``i``: NumPy array of values representing the real component of an IQ waveform.
* ``q``: NumPy array of values representing the imaginary component of an IQ waveform.
* ``assign``: Determines if waveform is assigned or not. Arguments are ``True`` (default) or ``False``.


``UXG``.\ **bin_pdw_file_builder**\ (*pdwList*)
"""""""""""""""""""""""""""""""""""""""""""""""

Builds a binary PDW file with a padding block to ensure the PDW section
begins at an offset of 4096 bytes (required by UXG).

See User's Guide>Streaming Use>PDW File Format section of Keysight UXG X-Series Agile Vector Adapter Online Documentation.

Arguments
"""""""""
* ``pdwList``: A list of PDWs. Argument is a tuple of lists where each list contains a single pulse descriptor word.
    * PDW Fields:
        * ``operation``: Type of PDW. Arguments are ``0`` (no operation), ``1`` (first PDW after reset), or ``2`` (reset, must be followed by PDW with operation ``1``).
        * ``freq``: CW frequency/chirp start frequency. Argument is a floating point value from ``50e6`` to ``20e9``. Default is ``1e9``.
        * ``phase``: Phase of carrier. Argument is an integer between ``0`` and ``360``.
        * ``startTimeSec``: Pulse start time. Argument is a float between ``0 ps`` and ``213.504 days`` in seconds with a resolution of ``1 ps``.
        * ``power``: Power in dBm. Argument is a float between ``-140`` and ``+23.835``.
        * ``markers``: Marker enable. Argument is a 12 bit binary value where each bit represents marker state. e.g. to activate marker 5 is ``0b000000100000``.
        * ``phaseControl``: Phase mode. Arguments are ``0`` (coherent) or ``1`` (continuous).
        * ``rfOff``: Control to turn off RF output. Arguments are ``0`` (RF **ON**) or ``1`` (RF **OFF**).
        * ``wIndex``: Waveform index file value that associates with a previously loaded waveform segment. Argument is an integer.
        * ``wfmMkrMask``: Enables waveform markers. Argument is a 4 bit binary value where each bit represents marker state. e.g. to activate all 4 markers is ``0xF``.

::

    rawPdw = ([1, 1e9, 0, 0,      0, 1, 0, 0, 0, 0xF],
              [0, 1e9, 0, 20e-6,  0, 0, 0, 0, 1, 0xF],
              [0, 1e9, 0, 120e-6, 0, 0, 0, 0, 2, 0xF],
              [2, 1e9, 0, 300e-6, 0, 0, 0, 0, 2, 0xF])

Returns
"""""""
* ``pdwFile``: A binary file that can be sent directly to the UXG memory using the ``MEMORY:DATA`` SCPI command or sent to the LAN streaming port using ``UXG``.\ *lanStream*\ .\ **send**


``UXG``.\ **csv_pdw_file_download**\ (*fileName*, *fields*, *data*)
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Builds a CSV PDW file, sends it into the UXG, and converts it to a binary PDW file.

Arguments
"""""""""
* ``fileName``: Name of the csv file without the extension. Argument is a string.
* ``fields``: Fields contained in the PDWs. Argument is a tuple of strings.
* ``values``: Values for each PDW. Argument is a tuple of lists where each list contains the values for a single pulse descriptor word.
    * See User's Guide>Streaming Use>CSV File Use>Streaming CSV File Creation section of Keysight UXG X-Series Agile Vector Adapter Online Documentation.

Returns
"""""""
* ``pdwFile``: A binary file that can be sent directly to the UXG memory using the ``MEMORY:DATA`` SCPI command or sent to the LAN streaming port using ``UXG``.\ *lanStream*\ .\ **send**
