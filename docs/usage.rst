#####
Usage
#####

To use pyarbtools in a project::

    import pyarbtools

pyarbtools is built from two primary submodules:

* :ref:`instruments`
* :ref:`wfmBuilder`

Supported instruments include:

* :ref:`M8190A` AWG
* :ref:`M8195A` AWG
* :ref:`M8196A` AWG
* :ref:`VSG`
    * E8267D PSG
    * N5182B MXG
    * N5172B EXG
* :ref:`UXG`
    * N5193A + N5194A combination

.. _instruments:

===============
**instruments**
===============

To use/control a signal generator, reate a class with the signal
generator type and the instrument's IP address::

    m8190a = pyarbtools.instruments.M8910A('192.168.1.12')
    n5182b = pyarbtools.instruments.VSG('192.168.1.13')

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

==========
**M8190A**
==========

**configure**
-------------
::

    M8190A.configure(res='wsp', clkSrc='int', fs=7.2e9, refSrc='axi', refFreq=100e6, out1='dac', out2='dac', func1='arb', func2='arb', cf1=2e9, cf2=2e9)

Sets the basic configuration for the M8190A and populates class
attributes accordingly. It should be called any time these settings are
changed (ideally *once* directly after creating the M8190A object).

**Arguments**

* ``res``: AWG resolution. Arguments are ``'wpr'``, ``'wsp'`` (default), ``'intx3'``, ``'intx12'``, ``'intx24'``, or ``'intx48'``.
* ``clkSrc``: Sample clock source. Arguments are ``'int'`` (default) or ``'ext'``.
* ``fs``: Sample rate. Argument is a floating point value from ``125e6`` to ``12e9``. Default is ``7.2e9``.
* ``refSrc``: Reference clock source. Arguments are ``'axi'`` (default), ``'int'``, ``'ext'``.
* ``refFreq``: Reference clock frequency. Argument is a floating point value from ``1e6`` to ``200e6`` in steps of ``1e6``. Default is ``100e6``.
* ``out1``, ``out2``: Output signal path for channel 1 and 2 respectively. Arguments are ``'dac'`` (default), ``'dc'``, ``'ac'``.
* ``func1``, ``func2``: Function of channel 1 and 2 respectively. Arguments are ``'arb'`` (default), ``'sts'``, or ``'stc'``.
* ``cf1``, ``cf2``: Carrier frequency of channel 1 and 2 respectively. This setting is only applicable if the digital upconverter is being used (``res`` arguments of ``'intx<#>'``). Arguments are floating point values between ``0`` and ``12e9``.

**Returns**

* None

**download_wfm**
----------------
::

    M8190A.download_wfm(wfm, ch=1, wfmID -> str)

Defines and downloads a waveform into the lowest available segment slot.

**Arguments**

* ``wfm``: NumPy array containing real waveform samples (not IQ).
* ``ch``: Channel to which waveform will be assigned. Arguments are ``1`` (default) or ``2``.
* ``name`` kwarg: Optional string argument to attach a name to your downloaded waveform segment.

**Returns**

* ``wfmID```: Waveform identifier used to specify which waveform is played using the ``.play()`` method.

**download_iq_wfm**
-------------------
::

    M8190A.download_iq_wfm(i, q, ch=1, name -> str)

Defines and downloads a waveform into the lowest available segment slot
while checking that the waveform meets minimum waveform length and
granularity requirements.

**Arguments**

* ``i``: NumPy array of values representing the real component of an IQ waveform.
* ``q``: NumPy array of values representing the imaginary component of an IQ waveform.
* ``ch``: Channel to which waveform will be assigned. Arguments are ``1`` (default) or ``2``.
* ``name`` kwarg: Optional string argument to attach a name to your downloaded waveform segment.

**Returns**

* ``wfmID``: Waveform identifier used to specify which waveform is played using the ``.play()`` method.

**play**
--------
::

    M8190A.play(wfmID=1, ch=1)

Selects waveform, turns on analog output, and begins continuous playback.

**Arguments**

* ``wfmID``: Segment index of the waveform to be loaded. Default is ``1``.
* ``ch``: Channel to be used for playback. Default is ``1``.

**Returns**

* None

**stop**
--------
::

    M8190A.stop(ch=1)

Turns off analog output and stops playback.

**Arguments**

* ``ch``: Channel to be stopped. Default is ``1``.

**Returns**

* None

.. _M8195A:

==========
**M8195A**
==========

**configure**
-------------
::

    M8195A.configure(dacMode='single', fs=64e9, refSrc='axi', refFreq=100e6, func='arb')

Sets the basic configuration for the M8195A and populates class
attributes accordingly. It should be called any time these settings are
changed (ideally *once* directly after creating the M8195A object).

**Arguments**

* ``dacMode``: Sets the DAC mode. Arguments are ``'single'`` (default), ``'dual'``, ``'four'``, ``'marker'``, ``'dcd'``, or ``'dcm'``.
* ``clkSrc``: Sample clock source. Arguments are ``'int'`` (default), ``'ext'``, ``'sclk1'``, or ``'sclk2'``.
* ``fs``: Sample rate. Argument is a floating point value from ``53.76e9`` to ``65e9``.
* ``refSrc``: Reference clock source. Arguments are ``'axi'`` (default), ``'int'``, ``'ext'``.
* ``refFreq``: Reference clock frequency. Argument is a floating point value from ``10e6`` to ``300e6`` in steps of ``1e6``. Default is ``100e6``.
* ``func``: Function of channels. Arguments are ``'arb'`` (default), ``'sts'``, or ``'stc'``.

**Returns**

* None

**download_wfm**
----------------
::

    M8195A.download_wfm(wfm, ch=1, name -> str)

Defines and downloads a waveform into the lowest available segment slot.

**Arguments**

* ``wfm``: NumPy array containing real waveform samples (not IQ).
* ``ch``: Channel to which waveform will be assigned. Arguments are ``1`` (default), ``2``, ``3``, or ``4``.
* ``name`` kwarg: Optional string argument to attach a name to your downloaded waveform segment.

**Returns**

* ``wfmID``: Waveform identifier used to specify which waveform is played using the ``.play()`` method.

**play**
--------
::

    M8195A.play(wfmID=1, ch=1)

Selects waveform, turns on analog output, and begins continuous playback.

**Arguments**

* ``wfmID``: Segment index of the waveform to be loaded. Default is ``1``.
* ``ch``: Channel to be used for playback. Arguments are ``1`` (default), ``2``, ``3``, ``4``.

**Returns**

* None

**stop**
--------
::

    M8195A.stop(ch=1)

Turns off analog output and stops playback.

**Arguments**

* ``ch``: Channel to be stopped. Default is ``1``.

**Returns**

* None

.. _M8196A:

==========
**M8196A**
==========

**configure**
-------------
::

    M8196A.configure(dacMode='single', fs=92e9, refSrc='axi', refFreq=100e6)

Sets the basic configuration for the M8196A and populates class
attributes accordingly. It should be called any time these settings are
changed (ideally *once* directly after creating the M8196A object).

**Arguments**

* ``dacMode``: Sets the DAC mode. Arguments are ``'single'`` (default), ``'dual'``, ``'four'``, ``'marker'``, or ``'dcmarker'``.
* ``fs``: Sample rate. Argument is a floating point value from ``82.24e9`` to ``93.4e9``.
* ``refSrc``: Reference clock source. Arguments are ``'axi'`` (default), ``'int'``, ``'ext'``.
* ``refFreq``: Reference clock frequency. Argument is a floating point value from ``10e6`` to ``17e9``. Default is ``100e6``.

**Returns**

* None

**download_wfm**
----------------
::

    M8196A.download_wfm(wfm, ch=1, name -> str)

Defines and downloads a waveform into the lowest available segment slot.

**Arguments**

* ``wfm``: NumPy array containing real waveform samples (not IQ).
* ``ch``: Channel to which waveform will be assigned. Arguments are ``1`` (default), ``2``, ``3``, or ``4``.
* ``name`` kwarg: Optional string argument to attach a name to your downloaded waveform segment.

**Returns**

* None

**play**
--------
::

    M8196A.play(ch=1)

Selects waveform, turns on analog output, and begins continuous playback.

**Arguments**

* ``ch``: Channel to be used for playback. Arguments are ``1`` (default), ``2``, ``3``, ``4``.

**Returns**

* None

**stop**
--------
::

    M8196A.stop(ch=1)

Turns off analog output and stops playback.

**Arguments**

* ``ch``: Channel to be stopped. Default is ``1``.

**Returns**

* None

.. _VSG:

=======
**VSG**
=======

**configure**
-------------
::

    VSG.configure(rfState=0, modState=0, cf=1e9, amp=-130, iqScale=70, refSrc='int', fs=200e6)

Sets the basic configuration for the VSG and populates class attributes
accordingly. It should be called any time these settings are changed
(ideally *once* directly after creating the VSG object).

**Arguments**

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
* ``fs``: Sample rate. Argument is a floating point whose range is instrument dependent.
    * EXG/MXG ``1e3`` to ``200e6``
    * PSG ``1`` to ``100e6``

**Returns**

* None

**download_iq_wfm**
-------------------
::

    VSG.download_iq_wfm(i, q, wfmID='wfm')

Defines and downloads a waveform into WFM1: memory directory and checks
that the waveform meets minimum waveform length and granularity
requirements.

**Arguments**

* ``i``: NumPy array of values representing the real component of an IQ waveform.
* ``q``: NumPy array of values representing the imaginary component of an IQ waveform.
* ``wfmID``: String containing the waveform name. Default is ``'wfm'``.

**Returns**

* ``wfmID``: Waveform identifier used to specify which waveform is played using the ``.play()`` method.

**play**
--------
::

    VSG.play(wfmID='wfm')

Selects waveform and activates arb mode, RF output, and modulation.

**Arguments**

* ``wfmID``: Name of the waveform to be loaded. Default is ``'wfm'``.

**Returns**

* None

**stop**
--------
::

    VSG.stop()

Deactivates arb mode, RF output, and modulation.

**Arguments**

* None

**Returns**

* None

.. _UXG:

=======
**UXG**
=======

**configure**
-------------
::

    UXG.configure(rfState=0, modState=0, cf=1e9, amp=-130, iqScale=70)

Sets the basic configuration for the UXG and populates class attributes
accordingly. It should be called any time these settings are changed
(ideally *once* directly after creating the UXG object).

**Arguments**

* ``rfState``: Turns the RF output state on or off. Arguments are ``0``/``'off'`` (default) or ``1``/``'on'``.
* ``modState``: Turns the modulation state on or off. Arguments are ``0``/``'off'`` (default) or ``1``/``'on'``.
* ``cf``: Sets the output carrier frequency. Argument is a floating point value from ``50e6`` to ``20e9``. Default is ``1e9``.
* ``amp``: Sets the output power. Argument is a floating point value from ``-120`` to ``+3``. Default is ``-120``.
* ``iqScale``: Sets the IQ scale factor. Argument is an integer from ``1`` to ``100``. Default is ``70``.

**Returns**

* None

**clear_memory**
----------------
::

    UXG.clear_memory()

Clears all waveform, pdw, and windex files. This function MUST be called
prior to downloading waveforms and making changes to an existing pdw file.

**Arguments**

* None

**Returns**

* None


**download_iq_wfm**
-------------------
::

    UXG.download_iq_wfm(i, q, wfmID='wfm')

Defines and downloads a waveform into WFM1: memory directory and checks
that the waveform meets minimum waveform length and granularity
requirements.

**Arguments**

* ``i``: NumPy array of values representing the real component of an IQ waveform.
* ``q``: NumPy array of values representing the imaginary component of an IQ waveform.
* ``wfmID``: String containing the waveform name. Default is ``'wfm'``.

**Returns**

* ``wfmID``: Waveform identifier used to specify which waveform is played using the ``.play()`` method.

**arb_play**
------------
::

    UXG.arb_play(wfmID='wfm')

Selects waveform and activates RF output, modulation, and arb mode.

**Arguments**

* ``wfmID``: Name of the waveform to be loaded. Default is ``'wfm'``.

**Returns**

* None

**arb_stop**
------------
::

    UXG.arb_stop()

Dectivates RF output, modulation, and arb mode.

**Arguments**

* None

**Returns**

* None

**stream_play**
---------------
::

    UXG.stream_play(pdwID='wfm', wIndexID=None)

Assigns pdw/windex, activates RF output, modulation, and streaming mode, and triggers streaming output.

**Arguments**

* ``pdwID``: Name of the PDW file to be loaded. Argument is a string. Default is ``'wfm'``.
* ``wIndexID``: Name of the waveform index file to be loaded. Argument is a string. Default is ``None``, which loads a waveform index file with the same name as the PDW file.

**Returns**

* None

**stream_stop**
---------------
::

    UXG.stream_stop()

Dectivates RF output, modulation, and streaming mode.

**Arguments**

* None

**Returns**

* None

**open_lan_stream**
-------------------
::

    UXG.open_lan_stream()

Open connection to port 5033 for LAN streaming to the UXG. Use this
directly prior to starting streaming control.

**Arguments**

* None

**Returns**

* None


**close_lan_stream**
--------------------
::

    UXG.close_lan_stream()

Close connection to port 5033 for LAN streaming on the UXG. Use this
after streaming is complete.

**Arguments**

* None

**Returns**

* None


**bin_pdw_file_builder**
------------------------
::

    UXG.bin_pdw_file_builder(operation=0, freq=1e9, phase=0, startTimeSec=0, power=0, markers=0, phaseControl=0, rfOff=0, wIndex=0, wfmMkrMask=0)

Builds a binary PDW file with a padding block to ensure the PDW section
begins at an offset of 4096 bytes (required by UXG).

See User's Guide>Streaming Use>PDW File Format section of Keysight UXG X-Series Agile Vector Adapter Online Documentation.

**Arguments**

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
        * ``wfmMkrMask``: Enables waveform markers. Argument is a 4 bit hex value where each bit represents marker state. e.g. to activate all 4 markers is ``0xF``.

::

    rawPdw = ([1, 1e9, 0, 0,      0, 1, 0, 0, 0, 0xF],
              [0, 1e9, 0, 20e-6,  0, 0, 0, 0, 1, 0xF],
              [0, 1e9, 0, 120e-6, 0, 0, 0, 0, 2, 0xF],
              [2, 1e9, 0, 300e-6, 0, 0, 0, 0, 2, 0xF])

**Returns**

* ``pdwFile``: A binary file that can be sent directly to the UXG memory using the ``MEMORY:DATA`` SCPI command or sent to the LAN streaming port using ``UXG``.\ *lanStream*\ .\ **send**


**csv_windex_file_download**
----------------------------
::

    UXG.csv_windex_file_download(windex)

Write header fields separated by commas and terminated with \n

**Arguments**

* ``windex``: Specifies waveform index file name and waveform names contained inside. Argument is a dict with 'fileName' and 'wfmNames' as keys. e.g. {'fileName': '<fileName>', 'wfmNames': ['name0', 'name1',... 'nameN']}

**Returns**

* None


**csv_pdw_file_download**
-------------------------
::

    UXG.csv_pdw_file_download(fileName, fields=('Operation', 'Time'), data=([1, 0], [2, 100e-6]))

Builds a CSV PDW file, sends it into the UXG, and converts it to a
binary PDW file. There are *a lot* of fields to choose from, but *you
do not need to specify all of them.* It really is easier than it looks.
See User's Guide>Streaming Use>CSV File Use>Streaming CSV File Creation
section of Keysight UXG X-Series Agile Vector Adapter Online
Documentation.

**Arguments**

* ``fileName``: Name of the csv file without the extension. Argument is a string.
* ``fields``: Fields contained in the PDWs. Argument is a tuple of strings.
* ``values``: Values for each PDW. Argument is a tuple of lists where each list contains the values for a single pulse descriptor word.
    * ``PDW Format``: Sets the PDW Format. Argument is a string ``'Auto'`` (automatic type selected), ``'Indexed'`` (Format 1, waveform description only), ``'Control'`` (Format 2, change markers and execute Marked Operations), or ``'Full'`` (Format 3, which specifies all possible values).
    * ``Operation``: Type of PDW. Arguments are ``0`` (no operation), ``1`` (first PDW after reset), or ``2`` (reset, must be followed by PDW with operation ``1``).
    * ``Time``: The start (50% of rise power) of the pulse with respect to Scenario Time. For Arb waveforms, the beginning of the waveform. Argument is a float between ``0 ps`` and ``213.504 days`` in seconds with a resolution of ``1 ps``.
    * ``Pulse Width``: The duration of the entire waveform. Argument is a float between ``0`` and ``68.72`` in seconds with a resolution of ``500 ps``. An argument of ``0`` uses the known waveform length.
    * ``Frequency``: CW frequency/chirp start frequency. Argument is a floating point value from ``50e6`` to ``20e9``. Default is ``1e9``.
    * ``Phase Mode``: Phase mode. Arguments are ``0`` (coherent) or ``1`` (continuous).
    * ``Phase``: Phase of carrier. Argument is an integer between ``-360`` and ``360``.
    * ``Maximum Power``: Power in dBm. Argument is a float between ``-140`` and ``+23.835``.
    * ``Power``: Power in dBm. Argument is a float between ``-140`` and ``+23.835``. If not specified, Maximum Power is used.
    * ``RF Off``: Control to turn off RF output. Arguments are ``0`` (RF **ON**) or ``1`` (RF **OFF**).
    * ``Markers``: Marker enable. Argument is a 12 bit hex spefication where each bit represents marker state. e.g. to activate marker 5 is ``0x020``
    * ``Marker Mask``: Enables waveform markers. Argument is a 4 bit hex value where each bit represents marker state. e.g. to activate all 4 markers is ``0xF``.
    * ``Index``: Waveform index file value that associates with a previously loaded waveform segment. Argument is an integer.
    * ``Name``: Specifies the name of a waveform file to play. This field overrides the ``Index`` field if specified. Argument is a string containing the desired waveform name.
    * ``New Waveform``: Documentation will be updated in an upcoming release.
    * ``Blank``: Controls blanking between PDW transitions. Arguments are strings, either ``'None'``, which doesn't blank the output during PDW transition, or ``'Auto'``, which blanks the output during PDW transition.
    * ``Zero/Hold``: Controls behavior of arb at the end of a waveform. Arguments are strings, either ``'Zero'``, which forces the arb output to go to 0, or ``'Hold'``, which holds the last waveform value until the beginning of the next PDW.
    * ``LO Lead``: Controls how long before the next PDW the LO begins to switch frequencies. Argument is an integer between ``0`` and ``500 ns``.
    * Documentation will be updated for the following fields/values in an upcoming release.
        * ``Width``: Specifies width of the pulse waveform generated at compile time.
        * ``Rise``: Specifies rise time of the pulse waveform generated at compile time.
        * ``Fall``: Specifies fall time of the pulse waveform generated at compile time.
        * ``Shape``: Specifies shape of the pulse waveform generated at compile time.
        * ``MOP``: Specifies modulation type of the pulse waveform generated at compile time.
        * ``Par1``: Specifies modulation parameters of the pulse waveform generated at compile time.
        * ``Par2``: Specifies modulation parameters of the pulse waveform generated at compile time.
        * ``Waveform Time Offset``: Specifies the start time offset of the pulse waveform generated at compile time.

::

    fileName = 'csv_pdw_test'
    fields = ('Operation', 'Time', 'Frequency', 'Zero/Hold', 'Markers', 'Name')
    data = ([1, 0    , 1e9, 'Hold', '0x1', 'waveform1'],
            [2, 10e-6, 1e9, 'Hold', '0x0', 'waveform2'])
    UXG.csv_pdw_file_download(fileName, fields, data)


**Returns**

* None


.. _wfmBuilder:

==============
**wfmBuilder**
==============

In addition to instrument control and communication, pyarbtools allows
you to create waveforms and load them into your signal generator or use
them as generic signals for DSP work::

    iChirp, qChirp = pyarbtools.wfmBuilder.chirp_generator(length=100e-6, fs=100e6, chirpBw=20e6)
    fs = 100e6
    symRate = 1e6
    i, q = digmod_prbs_generator(qpsk_modulator, fs, symRate, prbsOrder=9, filt=rrc_filter, alpha=0.35)


**chirp_generator**
-------------------
::

    wfmBuilder.chirp_generator(length=100e-6, fs=100e6, chirpBw=20e6, zeroLast=False):

Generates a symmetrical linear chirp (linear frequency modulated signal)
at baseband. Chirp direction is determined by the sign of chirpBw
(pos=up chirp, neg=down chirp).

**Arguments**

* ``length``: Length of the chirp. Argument is a float in units of seconds. Default is ``100e-6``.
* ``fs``: Sample rate used to create the signal. Argument is a float. Default is ``100e6``.
* ``chirpBw``: Total bandwidth of the chirp. Frequency range of resulting signal is ``-chirpBw/2`` to ``chirpBw/2``. Default is ``20e6``.
* ``zeroLast``: Allows user to force the last sample point to ``0``. Default is ``False``.

**Returns**

* ``i``: NumPy array of values representing the real component of the chirp waveform.
* ``q``: NumPy array of values representing the imaginary component of the chirp waveform.


**barker_generator**
--------------------
::

    wfmBuilder.barker_generator(length=100e-6, fs=100e6, code='b2', zeroLast=False)

Generates a baseband Barker phase coded signal.
See `Wikipedia article <https://en.wikipedia.org/wiki/Barker_code>`_ for
more information on Barker coding.


**Arguments**

* ``length``: Length of the pulse. Argument is a float in units of seconds. Default is ``100e-6``.
* ``fs``: Sample rate used to create the signal. Argument is a float. Default is ``100e6``.
* ``code``: Barker code order. Argument is a string containing ``'b2'`` (default), ``'b3'``, ``'b41'``, ``'b42'``, ``'b5'``, ``'b7'``, ``'b11'``, or ``'b13'``.
* ``zeroLast``: Allows user to force the last sample point to ``0``. Default is ``False``.

**Returns**

* ``i``: NumPy array of values representing the real component of the Barker pulse.
* ``q``: NumPy array of values representing the imaginary component of the Barker pulse.


**digmod_prbs_generator**
-------------------------
::

    digmod_prbs_generator(modType, fs, symRate, prbsOrder=9, filt=rrc_filter, alpha=0.35)

Generates a baseband modulated signal with a given modulation type and
transmit filter using PRBS data.


**Arguments**

* ``modType``: Type of modulation. Argument is a ``_modulator`` function.
    * ``bpsk_modulator``, generates a binary phase shift keyed signal.
    * ``qpsk_modulator``, generates a quadrature phase shift keyed signal.
    * ``psk8_modulator``, generates a 8-state phase shift keyed signal.
    * ``qam16_modulator``, generates a 16-state quadrature amplitude modulated signal.
    * ``qam32_modulator``, generates a 32-state quadrature amplitude modulated signal.
    * ``qam64_modulator``, generates a 64-state quadrature amplitude modulated signal.
    * ``qam128_modulator``, generates a 128-state quadrature amplitude modulated signal.
    * ``qam256_modulator``, generates a 256-state quadrature amplitude modulated signal.
* ``fs``: Sample rate used to create the signal. Argument is a float.
* ``symRate``: Symbol rate. Argument is a float.
* ``prbsOrder``: Order of the pseudorandom bit sequence used for the underlying data. Arguments are integers. ``7``, ``9`` (default), or ``13`` are recommended, anything much larger will take a long time to generate.
* ``filt``: Reference filter type. Argument is a ``_filter`` function.
    * ``rc_filter``: Creates the impulse response of a `raised cosine filter <https://en.wikipedia.org/wiki/Raised-cosine_filter>`_.
    * ``rrc_filter``: Creates the impulse response of a `root raised cosine filter <https://en.wikipedia.org/wiki/Root-raised-cosine_filter>`_. (default)
* ``alpha``: Excess filter bandwidth specification. Also known as roll-off factor, alpha, or beta. Argument is a float between ``0`` and ``1``. Default is ``0.35``.

**Returns**

* ``i``: NumPy array of values representing the real component of the digitally modulated signal.
* ``q``: NumPy array of values representing the imaginary component of the digitally modulated signal.


**multitone**
-------------
::

    multitone(start, stop, num, fs, phase='random')

Generates a multitone signal with given start/stop frequencies, number of tones, sample rate, and phase relationship.


**Arguments**

* ``start``: Start frequency, the first tone is at this freqency. Argument is a float. Must be < ``stop``.
* ``stop``: Stop frequency, the last tone is at this frequency. Argument is a float. Must be > ``start``.
* ``num``: Number of tones. Argument is an integer. Large values will slow down generation due to closer frequency spacing and resulting longer time requirements, use caution.
* ``fs``: Sample rate used to create the signal. Argument is a float.
* ``phase``: Phase relationship between tones. Arguments are ``'random'`` (default), ``'zero'``, ``'increasing'``, or ``'parabolic'``.

**Returns**

* ``i``: NumPy array of values representing the real component of the multitone signal.
* ``q``: NumPy array of values representing the imaginary component of the multitone signal.


**iq_correction**
-----------------
::

    iq_correction(i, q, inst, vsaIPAddress='127.0.0.1', vsaHardware='"Analyzer1"', cf=1e9, osFactor=4, thresh=0.4, convergence=2e-8):


Creates a 16-QAM signal from a signal generator at a user-selected
center frequency and sample rate. Symbol rate and effective bandwidth
of the calibration signal is determined by the oversampling rate in VSA.
Creates a VSA instrument, which receives the 16-QAM signal and extracts
& inverts an equalization filter and applies it to the user-defined
waveform.

**Arguments**

* ``i``: NumPy array of values representing the real component of the waveform to be corrected.
* ``q``: NumPy array of values representing the imaginary component of the waveform to be corrected.
* ``inst``: Instrument class of the generator to be used in the calibration. Must already be connected and configured. ``inst.fs`` is used as the basis for the calibration and ``inst.play()`` method is used.
* ``vsaIPAddress``: String containing the IP address of the VSA instance to be used in calibration. Default is ``'127.0.0.1'``.
* ``vsaHardware``: String containing the name of the hardware to be used by VSA. Name must be surrounded by double quotes (``"``). Default is ``'"Analyzer1"'``.
* ``cf``: Floating point value for the center frequency at which calibration takes place. Default is ``1e9``.
* ``osFactor``: Oversampling factor used by the digital demodulator in VSA. The larger the value, the narrower the bandwidth of the calibration. Effective bandwidth is roughly ``inst.fs / osFactor * 1.35``. Arguments are ``2``, ``4`` (default), ``5``, ``10``, or ``20``.
* ``thresh``: Defines the target EVM value that should be reached before extracting equalizer impulse response. Argument is a float < ``1.0``. Default is ``0.4``. Low values take longer to settle but result in better calibration.
* ``convergence``: Equalizer convergence value. Argument is a floating point value << 1. Default is ``2e-8``. High values settle more quickly but may become unstable. Lower values take longer to settle but tend to have better stability.

**Returns**

* ``iCorr``: NumPy array of values representing the real component of corrected signal.
* ``qCorr``: NumPy array of values representing the imaginary component of the corrected signal.
