#####
Usage
#####

To use pyarbtools in a project::

    import pyarbtools

**pyarbtools now has a GUI! To run it, navigate to the pyarbtools/ folder in the project directory and run** ``python gui.py``.

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
    * M9381A/M9383A
* :ref:`VectorUXG`
    * N5194A
* :ref:`AnalogUXG`
    * N5193A

.. _instruments:

===============
**instruments**
===============

To use/control a signal generator, create a class of the signal
generator's instrument type and enter the instrument's IP address
as the first argument::

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

    M8190A.configure(res='wsp', clkSrc='int', fs=7.2e9, refSrc='axi', refFreq=100e6, out1='dac', out2='dac', amp1=0.65, amp2=0.65, func1='arb', func2='arb', cf1=1e9, cf2=1e9)

Sets the basic configuration for the M8190A and populates class
attributes accordingly. It should be called any time these settings are
changed (ideally *once* directly after creating the M8190A object).

**Arguments**

* ``res`` ``(str)``: AWG resolution. Arguments are ``'wpr'`` (14 bit), ``'wsp'`` (12 bit) (default), ``'intx3'``, ``'intx12'``, ``'intx24'``, or ``'intx48'`` (intx resolutions are all 15 bit).
* ``clkSrc`` ``(str)``: Sample clock source. Arguments are ``'int'`` (default) or ``'ext'``.
* ``fs`` ``(float)``: Sample rate in Hz. Argument range is ``125e6`` to ``12e9``. Default is ``7.2e9``.
* ``refSrc`` ``(str)``: Reference clock source. Arguments are ``'axi'`` (default), ``'int'``, ``'ext'``.
* ``refFreq`` ``(float)``: Reference clock frequency in Hz. Argument range is ``1e6`` to ``200e6`` in steps of ``1e6``. Default is ``100e6``.
* ``out1``, ``out2`` ``(str)``: Output signal path for channel 1 and 2 respectively. Arguments are ``'dac'`` (default), ``'dc'``, ``'ac'``.
* ``amp1``, ``amp2`` ``(float)``: Output amplitude for channel 1 and 2 respectively. Argument range varies depending on output path chosen.
* ``func1``, ``func2`` ``(str)``: Function of channel 1 and 2 respectively. Arguments are ``'arb'`` (default), ``'sts'`` (sequence), or ``'stc'`` (scenario).
* ``cf1``, ``cf2`` ``(str)``: Carrier frequency in Hz of channel 1 and 2 respectively. This setting is only applicable if the digital upconverter is being used (``res`` arguments of ``'intx<#>'``). Argument range is ``0`` to ``12e9``.

**Returns**

* None

**download_wfm**
----------------
::

    M8190A.download_wfm(wfmData, ch=1, name='wfm', wfmFormat='iq', sampleMkr=0, syncMkr=0)

Defines and downloads a waveform into the lowest available segment slot.

**Arguments**

* ``wfmData`` ``(NumPy array)``: Array of waveform samples (either real or IQ).
* ``ch`` ``(int)``: Channel to which waveform will be assigned. Arguments are ``1`` (default) or ``2``.
* ``name`` ``(str)``: Name for downloaded waveform segment.
* ``wfmFormat`` ``(str)``: Format of the waveform being downloaded. Arguments are ``'iq'`` (default) or ``'real'``.
* ``sampleMkr`` ``(int)``: Index of the beginning of the sample marker. Currently, marker width is 240 samples.
* ``syncMkr`` ``(int)``: Index of the beginning of the sync marker. Currently, marker width is 240 samples.

**Returns**

* ``segment`` ``(int)``: Segment identifier used to specify which waveform is played using the ``.play()`` method.

**delete_segment**
------------------
::

    M8190A.delete_segment(wfmID=1, ch=1)

Deletes a waveform segment from the waveform memory.

**Arguments**

* ``wfmID`` ``(int)``: Segment number used to specify which waveform is deleted.
* ``ch`` ``(int)``: Channel from which waveform will be deleted. Arguments are ``1`` (default) or ``2``.

**Returns**

* None

**clear_all_wfm**
-----------------
::

    M8190A.clear_all_wfm()

Stops playback and deletes all waveform segments from the waveform memory.

**Arguments**

* None

**Returns**

* None

**play**
--------
::

    M8190A.play(wfmID=1, ch=1)

Selects waveform, turns on analog output, and begins continuous playback.

**Arguments**

* ``wfmID`` ``(int)``:  Waveform identifier, used to select waveform to be played. Default is ``1``.
* ``ch`` ``(int)``: Channel to be used for playback. Default is ``1``.

**Returns**

* None

**stop**
--------
::

    M8190A.stop(ch=1)

Turns off analog output and stops playback.

**Arguments**

* ``ch`` ``(int)``: Channel to be stopped. Default is ``1``.

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

* ``dacMode`` ``(str)``: Sets the DAC mode. Arguments are ``'single'`` (default), ``'dual'``, ``'four'``, ``'marker'``, ``'dcd'``, or ``'dcm'``.
* ``memDiv`` ``(str)``: Clock/memory divider rate. Arguments are ``1``, ``2``, or ``4``.
* ``fs`` ``(float)``: Sample rate in Hz. Argument range is ``53.76e9`` to ``65e9``.
* ``refSrc`` ``(str)``: Reference clock source. Arguments are ``'axi'`` (default), ``'int'``, ``'ext'``.
* ``refFreq`` ``(float)``: Reference clock frequency in Hz. Argument range is ``10e6`` to ``300e6`` in steps of ``1e6``. Default is ``100e6``.
* ``func`` ``(str)``: Function of channels. Arguments are ``'arb'`` (default), ``'sts'``, or ``'stc'``.

**Returns**

* None

**download_wfm**
----------------
::

    M8195A.download_wfm(wfmData, ch=1, name='wfm')

Defines and downloads a waveform into the lowest available segment slot.

**Arguments**

* ``wfmData`` ``(NumPy array)``: Array containing real waveform samples (not IQ).
* ``ch`` ``(int)``: Channel to which waveform will be assigned. Arguments are ``1`` (default), ``2``, ``3``, or ``4``.
* ``name`` ``(str)``: String providing a name for downloaded waveform segment.

**Returns**

* ``segment``: Segment number used to specify which waveform is played using the ``.play()`` method.

**delete_segment**
------------------
::

    M8195A.delete_segment(wfmID=1, ch=1)

Deletes a waveform segment from the waveform memory.

**Arguments**

* ``wfmID`` ``(int)``: Segment number used to specify which waveform is deleted.
* ``ch`` ``(int)``: Channel from which waveform will be deleted. Arguments are ``1`` (default), ``2``, ``3``, ``4``.

**Returns**

* None

**clear_all_wfm**
-----------------
::

    M8195A.clear_all_wfm()

Stops playback and deletes all waveform segments from the waveform memory.

**Arguments**

* None

**Returns**

* None

**play**
--------
::

    M8195A.play(wfmID=1, ch=1)

Selects waveform, turns on analog output, and begins continuous playback.

**Arguments**

* ``wfmID`` ``(int)``: Segment index of the waveform to be loaded. Default is ``1``.
* ``ch`` ``(int)``: Channel to be used for playback. Arguments are ``1`` (default), ``2``, ``3``, ``4``.

**Returns**

* None

**stop**
--------
::

    M8195A.stop(ch=1)

Turns off analog output and stops playback.

**Arguments**

* ``ch`` ``(int)``: Channel to be stopped. Default is ``1``.

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

* ``dacMode`` ``(str)``: Sets the DAC mode. Arguments are ``'single'`` (default), ``'dual'``, ``'four'``, ``'marker'``, or ``'dcmarker'``.
* ``fs`` ``(float)``: Sample rate. Argument range is ``82.24e9`` to ``93.4e9``.
* ``refSrc`` ``(str)``: Reference clock source. Arguments are ``'axi'`` (default), ``'int'``, ``'ext'``.
* ``refFreq`` ``(float)``: Reference clock frequency. Argument range is ``10e6`` to ``17e9``. Default is ``100e6``.

**Returns**

* None

**download_wfm**
----------------
::

    M8196A.download_wfm(wfmData, ch=1, name='wfm')

Defines and downloads a waveform into the lowest available segment slot.

**Arguments**

* ``wfmData`` ``(NumPy array)``: Array containing real waveform samples (not IQ).
* ``ch`` ``(int)``: Channel to which waveform will be assigned. Arguments are ``1`` (default), ``2``, ``3``, or ``4``.
* ``name`` ``(str)``: Name for downloaded waveform segment.

**Returns**

* ``segment`` ``(int)``: Segment number used to specify which waveform is played using the ``.play()`` method.

**delete_segment**
------------------
::

    M8196A.delete_segment(wfmID=1, ch=1)

Deletes a waveform segment from the waveform memory.

**Arguments**

* ``wfmID`` ``(int)``: Segment number used to specify which waveform is deleted.
* ``ch`` ``(int)``: Channel from which waveform will be deleted. Arguments are ``1`` (default), ``2``, ``3``, ``4``.

**Returns**

* None

**clear_all_wfm**
-----------------
::

    M8196A.clear_all_wfm()

Stops playback and deletes all waveform segments from the waveform memory.

**Arguments**

* None

**Returns**

* None

**play**
--------
::

    M8196A.play(ch=1)

Selects waveform, turns on analog output, and begins continuous playback.

**Arguments**

* ``ch`` ``(int)``: Channel to be used for playback. Arguments are ``1`` (default), ``2``, ``3``, ``4``.

**Returns**

* None

**stop**
--------
::

    M8196A.stop(ch=1)

Turns off analog output and stops playback.

**Arguments**

* ``ch`` ``(int)``: Channel to be stopped. Default is ``1``.

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

* ``rfState`` ``(int)``: Turns the RF output state on or off. Arguments are ``0`` (default) or ``1``.
* ``modState`` ``(int)``: Turns the modulation state on or off. Arguments are ``0`` (default) or ``1``.
* ``cf`` ``(float)``: Output carrier frequency in Hz. Argument range is instrument dependent. Default is ``1e9``.
    * EXG/MXG: ``9e3`` to ``6e9``
    * PSG: ``100e3`` to ``44e9``
* ``amp`` ``(float)``: Output power in dBm. Argument range is instrument dependent. Default is ``-130``.
    * EXG/MXG: ``-144`` to ``+26``
    * PSG: ``-130`` to ``+21``
* ``alcState`` ``(int)``: Turns the ALC (automatic level control) on or off. Arguments are ``1`` or ``0`` (default).
* ``iqScale`` ``(int)``: IQ scale factor in %. Argument range is ``1`` to ``100``. Default is ``70``.
* ``refSrc`` ``(str)``: Reference clock source. Arguments are ``'int'`` (default), or ``'ext'``.
* ``fs`` ``(float)``: Sample rate in Hz. Argument range is instrument dependent.
    * EXG/MXG: ``1e3`` to ``200e6``
    * PSG: ``1`` to ``100e6``

**Returns**

* None

**download_wfm**
----------------
::

    VSG.download_iq_wfm(wfmData, wfmID='wfm')

Defines and downloads a waveform into WFM1: memory directory and checks
that the waveform meets minimum waveform length and granularity
requirements.

**Arguments**

* ``wfmData`` ``(NumPy array)``: Array of values containing the complex sample pairs in an IQ waveform.
* ``wfmID`` ``(str)``: Name of the waveform to be downloaded. Default is ``'wfm'``.

**Returns**

* ``wfmID`` (string): Useful waveform name or identifier.

**delete_wfm**
--------------
::

    VSG.delete_wfm(wfmID)

Deletes a waveform from the waveform memory.

**Arguments**

* ``wfmID`` ``(str)``: Name of the waveform to be deleted.

**Returns**

* None

**clear_all_wfm**
-----------------
::

    VSG.clear_all_wfm()

Stops playback and deletes all waveforms from the waveform memory.

**Arguments**

* None

**Returns**

* None

**play**
--------
::

    VSG.play(wfmID='wfm')

Selects waveform and activates arb mode, RF output, and modulation.

**Arguments**

* ``wfmID`` ``(str)``: Name of the waveform to be loaded. Default is ``'wfm'``.

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

.. _AnalogUXG:

=============
**AnalogUXG**
=============

**configure**
-------------
::

    AnalogUXG.configure(rfState=0, modState=0, cf=1e9, amp=-130)


Sets the basic configuration for the UXG and populates class attributes
accordingly. It should be called any time these settings are changed
(ideally *once* directly after creating the UXG object).

**Arguments**

* ``rfState`` ``(int)``: Turns the RF output state on or off. Arguments are ``0`` (default) or ``1``.
* ``modState`` ``(int)``: Turns the modulation state on or off. Arguments are ``0`` (default) or ``1``.
* ``cf`` ``(float)``: Output carrier frequency in Hz. Argument range is ``10e6`` to ``40e9``. Default is ``1e9``.
* ``amp`` ``(float)``: Output power in dBm. Argument range is ``-130`` to ``+10``. Default is ``-130``.

**Returns**

* None

**open_lan_stream**
-------------------
::

    AnalogUXG.open_lan_stream()

Open connection to port 5033 for LAN streaming to the UXG. Use this
directly prior to starting streaming control.

**Arguments**

* None

**Returns**

* None


**close_lan_stream**
--------------------
::

    AnalogUXG.close_lan_stream()

Close connection to port 5033 for LAN streaming on the UXG. Use this
after streaming is complete.

**Arguments**

* None

**Returns**

* None

**stream_play**
---------------
::

    AnalogUXG.stream_play(pdwID='pdw')

Assigns pdw/windex, activates RF output, modulation, and streaming mode, and triggers streaming output.

**Arguments**

* ``pdwID`` ``(str)``: Name of the PDW file to be loaded. Default is ``'pdw'``.

**Returns**

* None

**stream_stop**
---------------
::

    AnalogUXG.stream_stop()

Dectivates RF output, modulation, and streaming mode.

**Arguments**

* None

**Returns**

* None

**bin_pdw_builder**
-------------------
::

    AnalogUXG.bin_pdw_builder(self, operation=0, freq=1e9, phase=0, startTimeSec=0, width=0, power=1, markers=0,
                        pulseMode=2, phaseControl=0, bandAdjust=0, chirpControl=0, code=0,
                        chirpRate=0, freqMap=0)

Builds a single format-1 PDW from a set of input parameters.
See User's Guide>Streaming Use>PDW Definitions section of Keysight UXG X-Series Agile Signal Generator `Online Documentation <http://rfmw.em.keysight.com/wireless/helpfiles/n519xa/n519xa.htm>`_.

**Arguments**
    * ``operation`` ``(int)``: Type of PDW. Arguments are ``0`` (no operation), ``1`` (first PDW after reset), or ``2`` (reset, must be followed by PDW with operation ``1``).
    * ``freq`` ``(float)``: CW frequency/chirp start frequency in Hz. Argument range is ``10e6`` to ``40e9``.
    * ``phase`` ``(int)``: Phase of carrier in degrees. Argument range is ``0`` to ``360``.
    * ``startTimeSec`` ``(float)``: Start time of the 50% rising edge power in seconds. Argument range is``0 ps`` to ``213.504 days`` with a resolution of ``1 ps``.
    * ``width`` ``(float)``: Width of the pulse from 50% rise power to 50% fall power in seconds. Argument range is ``4 ns`` to ``4.295 sec``.
    * ``relativePower`` ``(float)``: Linear scaling of output power in Vrms. Honestly just leave this as ``1``.
    * ``markers`` ``(int)``: 12-bit bit mask input of active markers (e.g. to activate marker 3, send the number 4, which is 0b000000000100 in binary).
    * ``pulseMode`` ``(int)``: Configures pulse mode. Arguments are ``0`` (CW), ``1`` (RF off), or ``2`` (Pulse enabled).
    * ``phaseControl`` ``(int)``: Phase mode. Arguments are ``0`` (coherent) or ``1`` (continuous).
    * ``bandAdjust`` ``(int)``: Controls how the frequency bands are selected. Arguments are ``0`` (CW switch points), ``1`` (upper band switch points), ``2`` (lower band switch points).
    * ``chirpControl`` ``(int)``: Controls the shape of the chirp. Arguments are ``0`` (stitched ramp chirp [don't use this]), ``1`` (triangle chirp), ``2`` (ramp chirp).
    * ``phaseCode`` ``(int)``: Selects hard-coded frequency/phase coding table index.
    * ``chirpRate`` ``(float)``: Chirp rate in Hz/us. Argument is an int.
    * ``freqMap`` ``(int)``: Selects frequency band map. Arguments are ``0`` (band map A), ``6`` (band map B).

**Returns**
    * ``(NumPy array)``: Single PDW that can be used to build a PDW file or streamed directly to the UXG.
::

    # PDW parameters
    numPdws = 1000
    pri = 100e-6
    width = 1e-6
    cf = 1e9
    pdw = []

    # Build PDWs as an array
    for i in range(numPdws):
        if i == 0:
            op = 1
        else:
            op = 0
        # Use pyarbtools function to create PDWs
        pdw.append(uxg.bin_pdw_builder(op, cf, 0, startTime, width, 1, 3, 2, 0, 0, 3, 0, 40000, 0))
        startTime += pri

**bin_pdw_file_builder**
------------------------
::

    AnalogUXG.bin_pdw_file_builder(pdwList)

Builds a binary PDW file with a padding block to ensure the PDW section
begins at an offset of 4096 bytes (required by UXG).

See User's Guide>Streaming Mode Use>PDW Definitions section of Keysight UXG X-Series Agile Signal Generator `Online Documentation <http://rfmw.em.keysight.com/wireless/helpfiles/n519xa/n519xa.htm>`_.

**Arguments**

* ``pdwList`` ``(list(list))``: A list of PDWs. Argument is a list of lists where each inner list contains the values for a single pulse descriptor word.
    * PDW Fields:
        * ``operation`` ``(int)``: Type of PDW. Arguments are ``0`` (no operation), ``1`` (first PDW after reset), or ``2`` (reset, must be followed by PDW with operation ``1``).
        * ``freq`` ``(float)``: CW frequency/chirp start frequency in Hz. Argument range is ``10e6`` to ``40e9``.
        * ``phase`` ``(int)``: Phase of carrier in degrees. Argument range is ``0`` to ``360``.
        * ``startTimeSec`` ``(float)``: Start time of the 50% rising edge power in seconds. Argument range is``0 ps`` to ``213.504 days`` with a resolution of ``1 ps``.
        * ``width`` ``(float)``: Width of the pulse from 50% rise power to 50% fall power in seconds. Argument range is ``4 ns`` to ``4.295 sec``.
        * ``relativePower`` ``(float)``: Linear scaling of output power in Vrms. Honestly just leave this as ``1``.
        * ``markers`` ``(int)``: 12-bit bit mask input of active markers (e.g. to activate marker 3, send the number 4, which is 0b000000000100 in binary).
        * ``pulseMode`` ``(int)``: Configures pulse mode. Arguments are ``0`` (CW), ``1`` (RF off), or ``2`` (Pulse enabled).
        * ``phaseControl`` ``(int)``: Phase mode. Arguments are ``0`` (coherent) or ``1`` (continuous).
        * ``bandAdjust`` ``(int)``: Controls how the frequency bands are selected. Arguments are ``0`` (CW switch points), ``1`` (upper band switch points), ``2`` (lower band switch points).
        * ``chirpControl`` ``(int)``: Controls the shape of the chirp. Arguments are ``0`` (stitched ramp chirp [don't use this]), ``1`` (triangle chirp), ``2`` (ramp chirp).
        * ``phaseCode`` ``(int)``: Selects hard-coded frequency/phase coding table index.
        * ``chirpRate`` ``(float)``: Chirp rate in Hz/us. Argument is an int.
        * ``freqMap`` ``(int)``: Selects frequency band map. Arguments are ``0`` (band map A), ``6`` (band map B).


::

    pdwName = 'pdw'
    pdwList = [[1, 980e6, 0, 0, 10e-6, 1, 0, 2, 0, 0, 3, 0, 4000000, 0],
               [2, 1e9, 0, 20e-6, 1e-6, 1, 0, 2, 0, 0, 0, 0, 0, 0]]
    pdwFile = uxg.bin_pdw_file_builder(pdwList)
    uxg.download_bin_pdw_file(pdwFile, pdwName=pdwName)

**Returns**

* ``(bytes)``: A binary file that can be sent directly to the UXG memory using ``AnalogUXG.bin_pdw_file_builder()`` method or sent to the LAN streaming port using ``AnalogUXG.lanStream.send()``

**download_bin_pdw_file**
-------------------------
::

    AnalogUXG.download_bin_pdw_file(pdwFile, pdwName='wfm')


Downloads binary PDW file to PDW directory in UXG.

**Arguments**

* ``pdwFile`` ``(bytes)``: A binary PDW file, ideally generated and returned by ``AnalogUXG.bin_pdw_file_builder()``.
* ``pdwName`` ``(str)``: The name of the PDW file.

**Returns**

* None

.. _VectorUXG:

=============
**VectorUXG**
=============

**configure**
-------------
::

    VectorUXG.configure(rfState=0, modState=0, cf=1e9, amp=-120, iqScale=70)

Sets the basic configuration for the UXG and populates class attributes
accordingly. It should be called any time these settings are changed
(ideally *once* directly after creating the UXG object).

**Arguments**

* ``rfState`` ``(int)``: Turns the RF output state on or off. Arguments are ``0`` (default) or ``1``.
* ``modState`` ``(int)``: Turns the modulation state on or off. Arguments are ``0`` (default) or ``1``.
* ``cf`` ``(float)``: Output carrier frequency in Hz. Argument range is ``50e6`` to ``20e9``. Default is ``1e9``.
* ``amp`` ``(float)``: Output power in dBm. Argument range is ``-120`` to ``+3``. Default is ``-120``.
* ``iqScale`` ``(int)``: IQ scale factor in %. Argument range is ``1`` to ``100``. Default is ``70``.

**Returns**

* None

**download_wfm**
----------------
::

    VectorUXG.download_iq_wfm(wfmData, wfmID='wfm')

Defines and downloads a waveform into WFM1: memory directory and checks
that the waveform meets minimum waveform length and granularity
requirements.

**Arguments**

* ``wfmData`` ``(NumPy array)``: Array of values containing the complex sample pairs in an IQ waveform.
* ``wfmID`` ``(str)``: String specifying the name of the waveform to be downloaded. Default is ``'wfm'``.

**Returns**

* ``wfmID`` ``(str)``: Name of waveform that has been downloaded.

**delete_wfm**
--------------
::

    VectorUXG.delete_wfm(wfmID)

Deletes a waveform from the waveform memory.

**Arguments**

* ``wfmID`` ``(str)``: Name of the waveform to be deleted.

**Returns**

* None

**clear_all_wfm**
-----------------
::

    VectorUXG.clear_all_wfm()

Stops playback and deletes all waveforms from the waveform memory.

**Arguments**

* None

**Returns**

* None

**arb_play**
------------
::

    VectorUXG.arb_play(wfmID='wfm')

Selects waveform and activates RF output, modulation, and arb mode.

**Arguments**

* ``wfmID`` ``(str)``: Name of waveform to be played. Default is ``'wfm'``.

**Returns**

* None

**arb_stop**
------------
::

    VectorUXG.arb_stop()

Dectivates RF output, modulation, and arb mode.

**Arguments**

* None

**Returns**

* None

**open_lan_stream**
-------------------
::

    VectorUXG.open_lan_stream()

Open connection to port 5033 for LAN streaming to the UXG. Use this
directly prior to starting streaming control.

**Arguments**

* None

**Returns**

* None


**close_lan_stream**
--------------------
::

    VectorUXG.close_lan_stream()

Close connection to port 5033 for LAN streaming on the UXG. Use this
after streaming is complete.

**Arguments**

* None

**Returns**

* None

**bin_pdw_builder**
-------------------
::

    VectorUXG.bin_pdw_builder(operation, freq, phase, startTimeSec, power, markers, phaseControl, rfOff, wIndex, wfmMkrMask)

Builds a single format-1 PDW from a set of parameters.
See User's Guide>Streaming Use>PDW File Format section of Keysight UXG X-Series Agile Vector Adapter `Online Documentation <http://rfmw.em.keysight.com/wireless/helpfiles/n519xa-vector/n519xa-vector.htm>`_.

**Arguments**
* ``operation`` ``(int)``: Type of PDW. Arguments are ``0`` (no operation), ``1`` (first PDW after reset), or ``2`` (reset, must be followed by PDW with operation ``1``).
* ``freq`` ``(float)``: CW frequency/chirp start frequency in Hz. Argument range is ``50e6`` to ``20e9``.
* ``phase`` ``(float)``: Phase of carrier in degrees. Argument range is ``0`` and ``360``.
* ``startTimeSec`` ``(float)``: Pulse start time in seconds. Argument range is ``0 ps`` and ``213.504 days`` with a resolution of ``1 ps``.
* ``power`` ``(float)``: Power in dBm. Argument range is ``-140`` and ``+23.835``.
* ``markers`` ``(int)``: Marker enable. Argument is a 12 bit binary value where each bit represents marker state. e.g. to activate marker 5 is ``0b000000100000``.
* ``phaseControl`` ``(int)``: Phase mode. Arguments are ``0`` (coherent) or ``1`` (continuous).
* ``rfOff`` ``(int)``: Control to turn off RF output. Arguments are ``0`` (RF **ON**) or ``1`` (RF **OFF**).
* ``wIndex`` ``(int)``: Waveform index file value that associates with a previously loaded waveform segment. Argument is an integer.
* ``wfmMkrMask`` ``(int)``: Enables waveform markers. Argument is a 4 bit hex value where each bit represents marker state. e.g. to activate all 4 markers is ``0xF``.

**Returns**
* ``(NumPy Array)``: Single PDW that can be used to build a PDW file or streamed directly to the UXG.

**bin_pdw_file_builder**
------------------------
::

    VectorUXG.bin_pdw_file_builder(pdwList)

Builds a binary PDW file with a padding block to ensure the PDW section
begins at an offset of 4096 bytes (required by UXG).

See User's Guide>Streaming Use>PDW File Format section of Keysight UXG X-Series Agile Vector Adapter `Online Documentation <http://rfmw.em.keysight.com/wireless/helpfiles/n519xa-vector/n519xa-vector.htm>`_.

**Arguments**

* ``pdwList`` ``(list(list))``: A list of PDWs. Argument is a list of lists where each inner list contains the values for a single pulse descriptor word.
* PDW Fields:
    * ``operation`` ``(int)``: Type of PDW. Arguments are ``0`` (no operation), ``1`` (first PDW after reset), or ``2`` (reset, must be followed by PDW with operation ``1``).
    * ``freq`` ``(float)``: CW frequency/chirp start frequency in Hz. Argument range is ``50e6`` to ``20e9``.
    * ``phase`` ``(float)``: Phase of carrier in degrees. Argument range is ``0`` and ``360``.
    * ``startTimeSec`` ``(float)``: Pulse start time in seconds. Argument range is ``0 ps`` and ``213.504 days`` with a resolution of ``1 ps``.
    * ``power`` ``(float)``: Power in dBm. Argument range is ``-140`` and ``+23.835``.
    * ``markers`` ``(int)``: Marker enable. Argument is a 12 bit binary value where each bit represents marker state. e.g. to activate marker 5 is ``0b000000100000``.
    * ``phaseControl`` ``(int)``: Phase mode. Arguments are ``0`` (coherent) or ``1`` (continuous).
    * ``rfOff`` ``(int)``: Control to turn off RF output. Arguments are ``0`` (RF **ON**) or ``1`` (RF **OFF**).
    * ``wIndex`` ``(int)``: Waveform index file value that associates with a previously loaded waveform segment. Argument is an integer.
    * ``wfmMkrMask`` ``(int)``: Enables waveform markers. Argument is a 4 bit hex value where each bit represents marker state. e.g. to activate all 4 markers is ``0xF``.

::

    rawPdw = ([1, 1e9, 0, 0,      0, 1, 0, 0, 0, 0xF],
              [0, 1e9, 0, 20e-6,  0, 0, 0, 0, 1, 0xF],
              [0, 1e9, 0, 120e-6, 0, 0, 0, 0, 2, 0xF],
              [2, 1e9, 0, 300e-6, 0, 0, 0, 0, 2, 0xF])

**Returns**

* ``pdwFile`` ``(bytes)``: A binary file that can be sent directly to the UXG memory using the ``MEMORY:DATA`` SCPI command or sent to the LAN streaming port using ``VectorUXG.lanStream.send()``


**csv_windex_file_download**
----------------------------
::

    VectorUXG.csv_windex_file_download(windex)

Write header fields separated by commas and terminated with ``\n``

**Arguments**

* ``windex`` ``(str)``: Specifies waveform index file name and waveform names contained inside. Argument is a dict with 'fileName' and 'wfmNames' as keys. e.g. {'fileName': '<fileName>', 'wfmNames': ['name0', 'name1',... 'nameN']}

**Returns**

* None


**csv_pdw_file_download**
-------------------------
::

    VectorUXG.csv_pdw_file_download(fileName, fields=['Operation', 'Time'], data=[[1, 0], [2, 100e-6]])

Builds a CSV PDW file, sends it into the UXG, and converts it to a
binary PDW file. There are *a lot* of fields to choose from, but *you
do not need to specify all of them.* It really is easier than it looks.
See User's Guide>Streaming Use>CSV File Use>Streaming CSV File Creation
section of Keysight UXG X-Series Agile Vector Adapter `Online Documentation <http://rfmw.em.keysight.com/wireless/helpfiles/n519xa-vector/n519xa-vector.htm>`_.

**Arguments**

* ``fileName`` ``(str)``: Name of the csv file without the extension.
* ``fields`` ``(list(str))``: Fields contained in the PDWs.
* ``values`` ``(list(list))``: Values for each PDW. Argument is a list of lists where each inner list contains the values for a single pulse descriptor word.
    * ``PDW Format`` ``(str)``: Sets the PDW Format. Arguments are ``'Auto'`` (automatic type selected), ``'Indexed'`` (Format 1, waveform description only), ``'Control'`` (Format 2, change markers and execute Marked Operations), or ``'Full'`` (Format 3, which specifies all possible values).
    * ``Operation`` ``(int)``: Type of PDW. Arguments are ``0`` (no operation), ``1`` (first PDW after reset), or ``2`` (reset, must be followed by PDW with operation ``1``).
    * ``Time`` ``(float)``: The start (50% of rise power) of the pulse with respect to Scenario Time. For Arb waveforms, the beginning of the waveform. Argument range is ``0 ps`` to ``213.504 days`` in seconds with a resolution of ``1 ps``.
    * ``Pulse Width`` ``(float)``: The duration of the entire waveform. Argument range is ``0`` to ``68.72`` in seconds with a resolution of ``500 ps``. An argument of ``0`` uses the known waveform length.
    * ``Frequency`` ``(float)``: CW frequency/chirp start frequency. Argument range is ``50e6`` to ``20e9``. Default is ``1e9``.
    * ``Phase Mode`` ``(int)``: Phase mode. Arguments are ``0`` (coherent) or ``1`` (continuous).
    * ``Phase`` ``(int)``: Phase of carrier. Argument range is ``-360`` and ``360``.
    * ``Maximum Power`` ``(float)``: Power in dBm. Argument range is ``-140`` to ``+23.835``.
    * ``Power`` ``(float)``: Power in dBm. Argument range is ``-140`` to ``+23.835``. If not specified, Maximum Power is used.
    * ``RF Off`` ``(int)``: Control to turn off RF output. Arguments are ``0`` (RF **ON**) or ``1`` (RF **OFF**).
    * ``Markers`` ``(int)``: Marker enable. Argument is a 12 bit hex spefication where each bit represents marker state. e.g. to activate marker 5 is ``0x020``
    * ``Marker Mask`` ``(int)``: Enables waveform markers. Argument is a 4 bit hex value where each bit represents marker state. e.g. to activate all 4 markers is ``0xF``.
    * ``Index`` ``(int)``: Waveform index file value that associates with a previously loaded waveform segment.
    * ``Name`` ``(str)``: Specifies the name of a waveform file to play. This field overrides the ``Index`` field if specified.
    * ``Blank`` ``(str)``: Controls blanking between PDW transitions. Arguments are ``'None'``, which doesn't blank the output during PDW transition, or ``'Auto'``, which blanks the output during PDW transition.
    * ``Zero/Hold`` ``(str)``: Controls behavior of arb at the end of a waveform. Arguments are ``'Zero'``, which forces the arb output to go to 0, or ``'Hold'``, which holds the last waveform value until the beginning of the next PDW.
    * ``LO Lead`` ``(float)``: Controls how long before the next PDW the LO begins to switch frequencies. Argument range is ``0`` to ``500`` in nanoseconds.
    * ``Width`` ``(float)``: Truncates waveform if ``Width`` is shorter than known waveform length or forces DAC to zero/hold last sample if ``Width`` is longer than known waveform length.
    * Documentation will be updated for the following fields/values in an upcoming release.
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
    VectorUXG.csv_pdw_file_download(fileName, fields, data)


**Returns**

* None

**stream_play**
---------------
::

    VectorUXG.stream_play(pdwID='wfm', wIndexID=None)

Assigns pdw/windex, activates RF output, modulation, and streaming mode, and triggers streaming output.

**Arguments**

* ``pdwID`` ``(str)``: Name of the PDW file to be loaded. Default is ``'wfm'``.
* ``wIndexID`` ``(str)``: Name of the waveform index file to be loaded. Default is ``None``, which loads a waveform index file with the same name as the PDW file.

**Returns**

* None

**stream_stop**
---------------
::

    VectorUXG.stream_stop()

Dectivates RF output, modulation, and streaming mode.

**Arguments**

* None

**Returns**

* None


.. _wfmBuilder:

==============
**wfmBuilder**
==============

In addition to instrument control and communication, pyarbtools allows
you to create waveforms and load them into your signal generator or use
them as generic signals for DSP work::

    iq = pyarbtools.wfmBuilder.chirp_generator(length=100e-6, fs=100e6, chirpBw=20e6)
    fs = 100e6
    symRate = 1e6
    iq = digmod_prbs_generator(qpsk_modulator, fs, symRate, prbsOrder=9, filt=rrc_filter, alpha=0.35)



**sine_generator**
------------------
::

    sine_generator(fs=100e6, freq=0, phase=0, wfmFormat='iq', zeroLast=False):

Generates a sine wave with configurable frequency and initial phase at baseband or RF.

**Arguments**

* ``fs`` ``(float)``: Sample rate used to create the signal in Hz. Argument is a float. Default is ``50e6``.
* ``freq`` ``(float)``: Sine wave frequency.
* ``phase`` ``(float)``: Initial phase offset. Argument range is ``0`` to ``360``.
* ``wfmFormat`` ``(str)``: Waveform format. Arguments are ``'iq'`` (default) or ``'real'``.
* ``zeroLast`` ``(bool)``: Allows user to force the last sample point to ``0``. Default is ``False``.

**Returns**

* ``(NumPy array)``: Array containing the complex or real values of the sine wave.

**am_generator**
----------------
::

    am_generator(fs=100e6, amDepth=50, modRate=100e3, cf=1e9, wfmFormat='iq', zeroLast=False):

Generates a linear sinusoidal AM signal of specified depth and modulation rate at baseband or RF.

**Arguments**

* ``fs`` ``(float)``: Sample rate used to create the signal in Hz. Default is ``50e6``.
* ``amDepth`` ``(int)``: Depth of AM in %. Argument range is ``0`` to ``100``. Default is ``50``.
* ``modRate`` ``(float)``: AM rate in Hz. Argument range is ``0`` to ``fs/2``. Default is ``100e3``.
* ``cf`` ``(float)``: Center frequency for ``'real'`` format waveforms. Default is ``1e9``.
* ``wfmFormat`` ``(str)``: Waveform format. Arguments are ``'iq'`` (default) or ``'real'``.
* ``zeroLast`` ``(bool)``: Allows user to force the last sample point to ``0``. Default is ``False``.

**Returns**

* ``(NumPy array)``: Array containing the complex or real values of the AM waveform.

**chirp_generator**
-------------------
::

    wfmBuilder.chirp_generator(fs=100e6, pWidth=10e-6, pri=100e-6, chirpBw=20e6, cf=1e9, wfmFormat='iq', zeroLast=False):

Generates a symmetrical linear chirped pulse at baseband or RF. Chirp direction is determined by the sign of chirpBw
(pos=up chirp, neg=down chirp).

**Arguments**

* ``fs`` ``(float)``: Sample rate used to create the signal in Hz. Default is ``100e6``.
* ``pWidth`` ``(float)``: Length of the pulse in seconds. Default is ``10e-6``. The pulse width will never be shorter than ``pWidth``, even if ``pri`` < ``pWidth``.
* ``pri`` ``(float)``: Pulse repetition interval in seconds. Default is ``100e-6``. If ``pri`` > ``pWidth``, the dead time will be included in the waveform.
* ``chirpBw`` ``(float)``: Total bandwidth of the chirp. Frequency range of resulting signal is ``-chirpBw/2`` to ``chirpBw/2``. Default is ``20e6``.
* ``cf`` ``(float)``: Center frequency for ``'real'`` format waveforms. Default is ``1e9``.
* ``wfmFormat`` ``(str)``: Waveform format. Arguments are ``'iq'`` (default) or ``'real'``.
* ``zeroLast`` ``(bool)``: Allows user to force the last sample point to ``0``. Default is ``False``.

**Returns**

* ``iq``/``real`` ``(NumPy array)``: Array containing the complex or real values of the chirped pulse.

**barker_generator**
--------------------
::

    wfmBuilder.barker_generator(fs=100e6, pWidth=100e-6, pri=100e-6, code='b2', cf=1e9, wfmFormat='iq', zeroLast=False)

Generates a Barker phase coded pulsed signal at RF or baseband.
See `Wikipedia article <https://en.wikipedia.org/wiki/Barker_code>`_ for
more information on Barker coding.


**Arguments**

* ``fs`` ``(float)``: Sample rate used to create the signal in Hz. Default is ``100e6``.
* ``pWidth`` ``(float)``: Length of the pulse in seconds. Default is ``10e-6``. The pulse width will never be shorter than ``pWidth``, even if ``pri`` < ``pWidth``.
* ``pri`` ``(float)``: Pulse repetition interval in seconds. Default is ``100e-6``. If ``pri`` > ``pWidth``, the dead time will be included in the waveform.
* ``code`` ``(str)``: Barker code order. Arguments are ``'b2'`` (default), ``'b3'``, ``'b41'``, ``'b42'``, ``'b5'``, ``'b7'``, ``'b11'``, or ``'b13'``.
* ``cf`` ``(float)``: Center frequency for ``'real'`` format waveforms. Default is ``1e9``.
* ``wfmFormat`` ``(str)``: Waveform format. Arguments are ``'iq'`` (default) or ``'real'``.
* ``zeroLast`` ``(bool)``: Allows user to force the last sample point to ``0``. Default is ``False``.

**Returns**

* ``iq``/``real`` ``(NumPy array)``: Array containing the complex or real values of the barker pulse.

**multitone**
-------------
::

    multitone(fs=100e6, spacing=1e6, num=11, phase='random', cf=1e9, wfmFormat='iq')

Generates a multitone signal with given tone spacing, number of tones, sample rate, and phase relationship.

**Arguments**

* ``fs`` ``(float)``: Sample rate used to create the signal in Hz. Default is ``100e6``.
* ``spacing`` ``(float)``: Tone spacing in Hz. There is currently no limit to ``spacing``, so beware of the compilation time for small spacings and beware of aliasing for large spacings.
* ``num`` ``(int)``: Number of tones. There is currently no limit to ``num``, so beware of long compilation times for large number of tones.
* ``phase`` ``(str)``: Phase relationship between tones. Arguments are ``'random'`` (default), ``'zero'``, ``'increasing'``, or ``'parabolic'``.
* ``cf`` ``(float)``: Center frequency for ``'real'`` format waveforms. Default is ``1e9``.
* ``wfmFormat`` ``(str)``: Waveform format. Arguments are ``'iq'`` (default) or ``'real'``.

**Returns**

* ``iq``/``real`` ``(NumPy array)``: Array containing the complex or real values of the multitone signal.

**digmod_prbs_generator**
-------------------------
::

    digmod_prbs_generator(fs=100e6, modType='qpsk', symRate=10e6, prbsOrder=9, filt=rrc_filter, alpha=0.35, zeroLast=False)

Generates a baseband modulated signal with a given modulation type and
transmit filter using PRBS data.


**Arguments**

* ``fs`` ``(float)``: Sample rate used to create the signal in Hz. Default is ``100e6``.
* ``modType`` ``(function handle)``: Type of modulation. Argument is a ``_modulator`` function handle.
    * ``bpsk_modulator``, generates a binary phase shift keyed signal.
    * ``qpsk_modulator``, generates a quadrature phase shift keyed signal.
    * ``psk8_modulator``, generates a 8-state phase shift keyed signal.
    * ``qam16_modulator``, generates a 16-state quadrature amplitude modulated signal.
    * ``qam32_modulator``, generates a 32-state quadrature amplitude modulated signal.
    * ``qam64_modulator``, generates a 64-state quadrature amplitude modulated signal.
    * ``qam128_modulator``, generates a 128-state quadrature amplitude modulated signal.
    * ``qam256_modulator``, generates a 256-state quadrature amplitude modulated signal.
* ``symRate`` ``(float)``: Symbol rate in Hz.
* ``prbsOrder`` ``(int)``: Order of the pseudorandom bit sequence used for the underlying data. Arguments of ``7``, ``9`` (default), or ``13`` are recommended, anything much larger will take a long time to generate.
* ``filt`` ``(function handle)``: Reference filter type. Argument is a ``_filter`` function handle.
    * ``rc_filter``: Creates the impulse response of a `raised cosine filter <https://en.wikipedia.org/wiki/Raised-cosine_filter>`_.
    * ``rrc_filter``: Creates the impulse response of a `root raised cosine filter <https://en.wikipedia.org/wiki/Root-raised-cosine_filter>`_. (default)
* ``alpha`` ``(float)``: Excess filter bandwidth specification. Also known as roll-off factor, alpha, or beta. Argument range is ``0`` to ``1``. Default is ``0.35``.
* ``zeroLast`` ``(bool)``: Allows user to force the last sample point to ``0``. Default is ``False``.

**Returns**

* ``iq`` ``(NumPy array)``: Array contianing the complex values of the digitally modulated signal.

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

* ``iq`` ``(NumPy array)``: Array contianing the complex values of the signal to be corrected.
* ``inst`` ``(pyarbtools.instrument.XXX)``: Instrument class of the generator to be used in the calibration. Must already be connected and configured. ``inst.fs`` is used as the basis for the calibration and ``inst.play()`` method is used.
* ``vsaIPAddress`` ``(str)``: IP address of the VSA instance to be used in calibration. Default is ``'127.0.0.1'``.
* ``vsaHardware`` ``(str)``: Name of the hardware to be used by VSA. Name must be surrounded by double quotes (``"``). Default is ``'"Analyzer1"'``.
* ``cf`` ``(float)``: Center frequency at which calibration takes place. Default is ``1e9``.
* ``osFactor`` ``(int)``: Oversampling factor used by the digital demodulator in VSA. The larger the value, the narrower the bandwidth of the calibration. Effective bandwidth is roughly ``inst.fs / osFactor * 1.35``. Arguments are ``2``, ``4`` (default), ``5``, ``10``, or ``20``.
* ``thresh`` ``(float)``: Defines the target EVM value that should be reached before extracting equalizer impulse response. Argument range is ``0`` to ``1.0``. Default is ``0.4``. Low values take longer to settle but result in better calibration.
* ``convergence`` ``(float)``: Equalizer convergence value. Argument should be << 1. Default is ``2e-8``. High values settle more quickly but may become unstable. Lower values take longer to settle but tend to have better stability.

**Returns**

* ``iqCorr`` ``(NumPy array)``: Array containing the complex values of corrected signal.
