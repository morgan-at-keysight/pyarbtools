"""
examples
Author: Morgan Allison, Keysight RF/uW Application Engineer
Provides example scripts for generic VSGs, UXG, and AWGs using
instrument classes from PyArbTools.
"""

import pyarbtools


def vsg_chirp_example(ipAddress):
    """Creates downloads, assigns, and plays out a chirp waveform with
    a generic VSG."""

    # Create VSG object
    vsg = pyarbtools.instruments.VSG(ipAddress, port=5025, reset=True)

    # Signal generator configuration variables
    amplitude = -5
    sampleRate = 50e6
    freq = 1e9

    # Configure signal generator
    vsg.configure(amp=amplitude, fs=sampleRate, cf=freq)
    vsg.sanity_check()

    # Waveform definition variables
    name = 'chirp'
    pWidth = 10e-6
    bw = 40e6
    pri = 100e-6

    # Create waveform
    iq = pyarbtools.wfmBuilder.chirp_generator(fs=vsg.fs, pWidth=pWidth, pri=pri, chirpBw=bw)

    # Download and play waveform
    vsg.download_wfm(iq, name)
    vsg.play(name)

    # Check for erros and gracefully disconnect
    vsg.err_check()
    vsg.disconnect()


def vsg_dig_mod_example(ipAddress):
    """Generates and plays 1 MHz 16 QAM signal with 0.35 alpha RRC filter
    @ 1 GHz CF with a generic VSG."""

    # Create VSG object
    vsg = pyarbtools.instruments.VSG(ipAddress, port=5025, timeout=15, reset=True)

    # Signal generator configuration variables
    amplitude = -5
    sampleRate = 200e6
    freq = 1e9

    # Configure signal generator
    vsg.configure(amp=amplitude, fs=sampleRate, cf=freq)
    vsg.sanity_check()
    vsg.err_check()

    # Waveform definition variables
    name = '10MHZ_16QAM'
    symRate = 10e6
    modType = 'qam16'

    # Create waveform
    iq = pyarbtools.wfmBuilder.digmod_generator(fs=vsg.fs, modType=modType, symRate=symRate, filt='rootraisedcosine')

    # Download and play waveform
    vsg.download_wfm(iq, wfmID=name)
    vsg.play(name)

    # Check for erros and gracefully disconnect
    vsg.err_check()
    vsg.disconnect()


def vsg_am_example(ipAddress):
    """Generates an AM tone with the IQ modulator in a generic VSG."""

    # Create VSG object
    vsg = pyarbtools.instruments.VSG(ipAddress, reset=True)

    # Signal generator configuration variables
    amplitude = -5
    sampleRate = 100e6
    freq = 1e9

    # Configure signal generator
    vsg.configure(amp=amplitude, fs=sampleRate, cf=freq)
    vsg.sanity_check()
    vsg.err_check()

    # Waveform definition variables
    name = 'CUSTOM_AM'
    amRate = 100e3
    amDepth = 75

    # Create waveform
    iq = pyarbtools.wfmBuilder.am_generator(fs=vsg.fs, amDepth=amDepth, modRate=amRate)

    # Download and play waveform
    vsg.download_wfm(iq, wfmID=name)
    vsg.play(name)

    # Check for errors and gracefully disconnect
    vsg.err_check()
    vsg.disconnect()


def vsg_mtone_example(ipAddress):
    """Generates a mutlitone signal on a generic VSG."""

    vsg = pyarbtools.instruments.VSG(ipAddress, reset=True)

    # Signal generator configuration variables
    amplitude = -5
    sampleRate = 100e6
    freq = 1e9

    # Configure signal generator
    vsg.configure(amp=amplitude, fs=sampleRate, cf=freq)
    vsg.sanity_check()
    vsg.err_check()

    # Waveform definition variables
    name = 'MULTITONE'
    numTones = 400
    toneSpacing = 100e3

    # Create waveform
    iq = pyarbtools.wfmBuilder.multitone_generator(fs=vsg.fs, spacing=toneSpacing, num=numTones)

    # Download and play waveform
    vsg.download_wfm(iq, wfmID=name)
    vsg.play(name)

    # Check for errors and gracefully disconnect
    vsg.err_check()
    vsg.disconnect()


def m8190a_simple_wfm_example(ipAddress):
    """Sets up the M8190A and creates, downloads, assigns, and plays
    out a simple sine waveform from the AC output port."""

    res = 'wsp'
    fs = 10e9
    output = 'ac'
    amp = 0.6
    cf = 1e9
    wfmName = 'sine'

    awg = pyarbtools.instruments.M8190A(ipAddress, reset=True)
    awg.configure(res=res, fs=fs, out1=output, amp1=amp)

    # Create simple sinusoidal waveform
    real = pyarbtools.wfmBuilder.sine_generator(fs=awg.fs, freq=cf, wfmFormat='real')

    # Define segment 1 and populate it with waveform data.
    segment = awg.download_wfm(real, ch=1, name=wfmName, wfmFormat='real')

    # Assign segment to channel 1 and start playback.
    awg.play(ch=1, wfmID=segment)

    # Check for errors and gracefully disconnect.
    awg.err_check()
    awg.disconnect()


def m8190a_duc_dig_mod_example(ipAddress):
    """Creates a 10 MHz 16 QAM waveform using digital upconversion on the M8190A."""

    res = 'intx3'
    cf = 1e9
    output = 'ac'

    modType = 'qam16'
    symRate = 10e6
    wfmName = '10MHz_16QAM'

    awg = pyarbtools.instruments.M8190A(ipAddress, port=5025, reset=True)
    awg.configure(res=res, cf1=cf, out1=output)

    # Create 16 QAM signal.
    iq = pyarbtools.wfmBuilder.digmod_generator(fs=awg.bbfs, modType=modType, symRate=symRate, filt='rootraisedcosine')

    # Download waveform to memory
    segment = awg.download_wfm(iq, ch=1, name=wfmName, wfmFormat='iq')

    # Assign segment to channel 1 and start playback
    awg.play(wfmID=segment, ch=1)
    awg.err_check()
    awg.disconnect()


def m8190a_duc_chirp_example(ipAddress):
    """Creates a 40 MHz chirped pulse using digital upconversion on the M8190A."""

    wfmName = 'chirp'
    res = 'intx3'
    fs = 7.2e9
    output = 'ac'
    cf = 1e9

    pw = 10e-6
    pri = 100e-6
    bw = 40e6

    awg = pyarbtools.instruments.M8190A(ipAddress, reset=True)
    awg.configure(res=res, fs=fs, out1=output, cf1=cf)

    # Create chirp waveform.
    iq = pyarbtools.wfmBuilder.chirp_generator(fs=awg.bbfs, pWidth=pw, pri=pri, chirpBw=bw, wfmFormat='iq')

    # Interleave i and q into a single waveform and download to segment 1.
    segment = awg.download_wfm(iq, ch=1, name=wfmName, wfmFormat='iq')

    # Assign segment to channel 1 and start playback.
    awg.play(wfmID=segment, ch=1)

    # Check for errors and gracefully disconnect.
    awg.err_check()
    awg.disconnect()


def m8195a_simple_wfm_example(ipAddress):
    """Sets up the M8195A and creates, downloads, assigns, and plays
    out a simple sine waveform from the AC output port."""

    # Create M8195A object
    awg = pyarbtools.instruments.M8195A(ipAddress, reset=True)

    # AWG configuration variables
    dacMode = 'dual'
    fs = 64e9
    awg.configure(dacMode=dacMode, fs=fs, amp1=100e-3)

    # Waveform definition variables
    sineFreq = 1e9
    wfmFormat = 'real'

    # Define a waveform, ensuring min length and granularity requirements are met
    real = pyarbtools.wfmBuilder.sine_generator(fs=awg.fs, freq=sineFreq, wfmFormat=wfmFormat)

    # Download waveform to AWG and get waveform identifier
    wfmID = awg.download_wfm(real, ch=1)

    # Play waveform using identifier
    awg.play(wfmID=wfmID, ch=1)

    # Check for errors and gracefully disconnect.
    awg.err_check()
    awg.disconnect()


def vector_uxg_dig_mod_example(ipAddress):
    """Generates and plays 10 MHz 64 QAM signal with 0.35 alpha RRC filter
    @ 1 GHz CF with vector UXG."""

    # Create vector UXG object
    uxg = pyarbtools.instruments.VectorUXG(ipAddress, port=5025, timeout=10, reset=True)

    # UXG configuration variables
    amplitude = -5
    output = 1
    freq = 1e9

    # Configure UXG
    uxg.configure(amp=amplitude, rfState=output, cf=freq)

    # Waveform definition variables
    wfmName = '10M_16QAM'
    modType = 'qam16'
    symRate = 10e6

    # Create waveform
    iq = pyarbtools.wfmBuilder.digmod_generator(fs=uxg.fs, modType=modType, symRate=symRate, filt='rootraisedcosine')

    # Download and play waveform
    uxg.download_wfm(iq, wfmID=wfmName)
    uxg.play(wfmID=wfmName)

    # Check for errors and gracefully disconnect
    uxg.err_check()
    uxg.disconnect()


def vector_uxg_pdw_example(ipAddress):
    """Creates and downloads a chirp waveform, defines a simple pdw csv
    file, and loads that pdw file into the UXG, and plays it out."""

    uxg = pyarbtools.instruments.VectorUXG(ipAddress, port=5025, timeout=10, reset=True)

    # UXG configuration variables
    amplitude = -5
    output = 1
    freq = 1e9

    uxg.configure(amp=amplitude, rfState=output, cf=freq)

    """Configure pdw markers. These commands will assign a TTL pulse
    at the beginning of each PDW. The trigger 2 output will only be
    active if the Marker field for a given PDW is specified as '0x1'"""
    uxg.write('stream:markers:pdw1:mode stime')
    uxg.write('route:trigger2:output pmarker1')

    # Waveform definition variables
    pWidth = 10e-6
    chirpBw = 40e6
    wfmName = 'CHIRP'

    # Create and download chirp waveform
    iq = pyarbtools.wfmBuilder.chirp_generator(fs=uxg.fs, pWidth=pWidth, pri=pWidth, chirpBw=chirpBw, zeroLast=True)
    uxg.download_wfm(iq, wfmName)

    # Define and generate csv pdw file
    pdwName = 'basic_chirp'

    # 'fields' list define the PDW fields positionally
    fields = ['Operation', 'Time', 'Frequency', 'Zero/Hold', 'Markers', 'Name']

    # 'data' is a list of lists, where each inner list defines
    # the PDW using positional values for the fields defined above
    data = [[1, 0,      975e6, 'Hold', '0x1', wfmName],
            [0, 30e-6, 1025e6, 'Hold', '0x0', wfmName],
            [2, 60e-6,    1e9, 'Hold', '0x0', wfmName]]

    # Note: the last PDW starting with a '2' in the 'Operation'
    # field marks the end of the PDW stream and does not play

    # Download PDW file using an intermediate csv file
    uxg.csv_pdw_file_download(pdwName, fields, data)

    # Begin PDW streaming
    uxg.stream_play(pdwID=pdwName)

    # Check for errors and gracefully disconnect
    uxg.err_check()
    uxg.disconnect()


def vector_uxg_lan_streaming_example(ipAddress):
    """Creates and downloads iq waveforms & a waveform index file,
    builds a PDW file, configures LAN streaming, and streams the PDWs
    to the UXG.

    This streams five pulses. To capture this, PDW 1 will output a hardware
    trigger on the N5194A trigger output 2.
    """

    # Create vector UXG object
    uxg = pyarbtools.instruments.VectorUXG(ipAddress, port=5025, timeout=10, reset=True)

    # UXG configuration variables
    amplitude = -5
    output = 0
    modulation = 1

    # Configure UXG and clear all waveform memory
    uxg.configure(amp=amplitude, rfState=output, modState=modulation)
    uxg.clear_all_wfm()

    # Waveform definition variables, three chirps of the same bandwidth and different lengths
    bandwidth = 100e6
    lengths = [10e-6, 50e-6, 100e-6]
    wfmNames = []
    fileName = 'chirps'

    # Create and download waveforms to UXG and save a list of names used for each wfm
    for l in lengths:
        iq = pyarbtools.wfmBuilder.chirp_generator(fs=uxg.fs, pWidth=l, pri=l, chirpBw=bandwidth, wfmFormat='iq', zeroLast=True)
        uxg.download_wfm(iq, f'{l}_100MHz_CHIRP')
        wfmNames.append(f'{l}_100MHz_CHIRP')

    # Create waveform index file using the file name and wfm names we saved
    windex = {'fileName': fileName, 'wfmNames': wfmNames}

    # Download waveform index file so the UXG knows what
    # waveforms correspond to the wIndex field in the PDWs
    uxg.csv_windex_file_download(windex)

    # Create PDWs
    # operation, freq, phase, startTimeSec, power, markers, phaseControl, rfOff, wIndex, wfmMkrMask
    # See documentation for bin_pdw_file_builder for more info
    rawPdw = [[1, 1e9, 0, 0,      -10, 1, 0, 0, 0, 0xF],
              [0, 1e9, 0, 20e-6,  -10, 0, 0, 0, 0, 0xF],
              [0, 1e9, 0, 40e-6,  -10, 0, 0, 0, 1, 0xF],
              [0, 1e9, 0, 100e-6, -10, 0, 0, 0, 1, 0xF],
              [0, 1e9, 0, 160e-6, -10, 0, 0, 0, 2, 0xF],
              [2, 1e9, 0, 300e-6, -10, 0, 0, 0, 2, 0xF]]

    # Note: the last PDW starting with a '2' in the 'Operation'
    # field marks the end of the PDW stream and does not play

    pdwFile = uxg.bin_pdw_file_builder(rawPdw)

    # Separate pdwFile into header and data portions (AUTOMATE THIS)
    header = pdwFile[:4096]
    data = pdwFile[4096:]

    # Configure LAN streaming using SCPI commands (AUTOMATE THIS)
    uxg.write('stream:source lan')
    uxg.write('stream:trigger:play:file:type continuous')
    uxg.write('stream:trigger:play:file:type:continuous:type trigger')
    uxg.write('stream:trigger:play:source bus')

    # Route PDW Marker 1 to N5194A trigger 2 output using SCPI commands
    uxg.write('route:connectors:trigger2:output pmarker1')

    # Load waveform index file and select it as the reference file for streaming
    uxg.write(f'memory:import:windex "{windex["fileName"]}.csv","{windex["fileName"]}"')
    uxg.write(f'stream:windex:select "{windex["fileName"]}"')

    # Clear the stream header to prepare for a new stream
    uxg.write('stream:external:header:clear')

    """ADVANCED"""
    # The esr=False argument in binblockwrite() allows you to send your own
    # read/query after writing the binary block data rather than the
    # default *ESR? query that is automatically appended for error checking.

    # This is required because the SCPI command is a query rather than a command,
    # which is uncommon for commands that send binary block data
    uxg.binblockwrite(f'stream:external:header? ', header, esr=False)
    if uxg.read() != '+0':
        raise pyarbtools.error.VSGError('stream:external:header? response invalid. This should never happen.')

    # Configure LAN streaming and send PDWs
    # uxg.write('stream:state on')
    uxg.open_lan_stream()

    # If RF is turned on before this point a CW tone will appear before pulses
    uxg.configure(rfState=1, modState=1)

    # Use the separate LAN socket specifically opened for PDW streaming
    uxg.lanStream.send(data)

    # Ensure everything is synchronized
    uxg.query('*opc?')

    # Begin streaming
    uxg.write('stream:trigger:play:immediate')

    # Check for errors and gracefully disconnect.
    uxg.err_check()
    uxg.disconnect()


def analog_uxg_pdw_example(ipAddress):
    """Defines a pdw file for a chirp, and loads the
     pdw file into the UXG, and plays it out."""

    # Create analog UXG object
    uxg = pyarbtools.instruments.AnalogUXG(ipAddress, port=5025, timeout=10, reset=False)

    # UXG configuration variables
    output = 0
    modulation = 1
    freq = 1e9
    amplitude = -5

    # Configure UXG
    uxg.configure(rfState=output, modState=modulation, cf=freq, amp=amplitude)

    # Define and generate binary pdw file
    pdwName = 'analog'
    # Fields:
    # operation, freq, phase, startTimeSec, width, power, markers,
    # pulseMode, phaseControl, bandAdjust, chirpControl, fpc_code_selection,
    # chirpRate, freqMap
    pdwList = [[1, 980e6,  0, 0,     10e-6, 1, 0, 2, 0, 0, 3, 0, 4000000, 0],
               [0, 1e9,    0, 20e-6, 15e-6, 1, 0, 2, 0, 0, 0, 1, 0,       0],
               [0, 1.01e9, 0, 40e-6, 20e-6, 1, 0, 2, 0, 0, 0, 2, 0,       0],
               [2, 1e9,    0, 80e-6, 5e-6,  1, 0, 2, 0, 0, 0, 1, 0,       0]]
    pdwFile = uxg.bin_pdw_file_builder(pdwList)

    # Note: the last PDW starting with a '2' in the 'Operation'
    # field marks the end of the PDW stream and does not play

    # Download PDW file
    uxg.download_bin_pdw_file(pdwFile, pdwName=pdwName)
    uxg.err_check()

    # Begin streaming
    uxg.stream_play(pdwID=pdwName)

    # Check for errors and gracefully disconnect
    uxg.err_check()
    uxg.disconnect()


def wfm_to_vsa_example(ipAddress):
    """This function creates a "perfect" digitally modulated waveform, exports it to a csv file,
    recalls it into VSA, and configures VSA to analyze it."""

    # Waveform creation variables
    symRate = 10e6
    fs = 100e6
    modType = 'qam256'
    psFilter = 'rootraisedcosine'
    alpha = 0.35
    fileName = 'C:\\Temp\\wfm.csv'
    fileFormat = 'csv'

    print('Creating waveform.')
    # This is the new digital modulation waveform creation function
    data = pyarbtools.wfmBuilder.digmod_generator(fs=fs, symRate=symRate, modType=modType, filt=psFilter, numSymbols=10000, alpha=alpha)

    print('Exporting waveform.')
    # Export the waveform to a csv file
    pyarbtools.wfmBuilder.export_wfm(data, fileName, True, fs)

    print('Setting up VSA.')
    # Create VSA object
    vsa = pyarbtools.vsaControl.VSA(ipAddress, vsaHardware=None, timeout=10, reset=False)

    # Select a digital demod measurement and configure it to measure the saved waveform
    vsa.set_measurement('ddemod')
    if psFilter.lower() == 'rootraisedcosine':
        mFilter = 'rootraisedcosine'
        rFilter = 'raisedcosine'
    elif psFilter.lower() == 'raisedcosine':
        mFilter = 'none'
        rFilter = 'raisedcosine'
    else:
        raise Exception('Invalid filter type chosen.')

    # Configure digital demodulation in VSA
    vsa.configure_ddemod(amp=0, modType=modType, symRate=symRate, measFilter=mFilter, refFilter=rFilter, filterAlpha=alpha,
                         measLength=1000, eqState=False)

    # Recall csv file we exported earlier
    vsa.recall_recording(fileName, fileFormat=fileFormat)

    # Perform a single-shot replay in VSA
    vsa.acquire_single()

    # Check for errors and gracefully disconnect
    vsa.err_check()
    vsa.disconnect()


def vsa_vector_example(ipAddress):
    """Connects to a running instance of VSA, configures a vector measurement, and prints out settings."""

    # Vector configuration settings
    cf = 1e9
    span = 20e6
    amp = -5
    time = 100e-6

    vsa = pyarbtools.vsaControl.VSA(ipAddress)
    vsa.set_measurement('vector')
    vsa.configure_vector(cf=cf, span=span, amp=amp, time=time)
    vsa.acquire_single()
    vsa.sanity_check()

    # Check for errors and gracefully disconnect
    vsa.err_check()
    vsa.disconnect()


def vxg_mat_import_example(ipAddress, fileName):
    """Imports an IQ waveform from a .mat file, loads it into the VXG, and plays it out."""

    """
    import_mat() takes in a .mat file with an array containing the waveform data, and optional variables for
    waveform identifier, sample rate, and waveform type.
    The .mat file used as an example has the following variables:
        iqdata (complex array): Array containing waveform samples
        fs (float): Sample rate at which waveform was created
        wfmID (string): Name of waveform.
    In this case, we know the variable 'iqdata' in the .mat file contains our complex waveform data, so we use 'iqdata' as 
    the 'targetVariable' argument.
    import_mat() returns a dict with 'data', 'fs', 'wfmID', and 'wfmFormat' members.
    If the .mat file contains the optional metadata variables, the corresponding dict members will be populated accordingly.
    """

    # Load waveform from .mat file
    wfmDict = pyarbtools.wfmBuilder.import_mat(fileName, targetVariable='iqdata')

    # Create VXG object
    vxg = pyarbtools.instruments.VXG(ipAddress)

    # Configure vxg based on variables imported from the .mat file
    vxg.configure(cf2=1e9, fs2=wfmDict['fs'], rfState2=1, amp2=0)

    # Download waveform to vxg by passing the complex array of samples and the waveform name from the dict
    vxg.download_wfm(wfmDict['data'], wfmID=wfmDict['wfmID'])

    # Play out the waveform by referencing the waveform name from the dict
    vxg.play(wfmID=wfmDict['wfmID'], ch=2)

    vxg.disconnect()


def gui_example():
    """Starts experimental PyArbTools GUI"""
    pyarbtools.gui.main()


def main():
    """Uncomment the example you'd like to run. For each example,
    replace the IP address with one that is appropriate for your
    instrument(s)."""
    # ipAddress = '192.168.1.17'
    ipAddress = '141.121.151.242'
    matFilePath = 'C:\\users\\moalliso\\desktop\\10mhz16qamat100mhz.mat'

    # m8190a_simple_wfm_example(ipAddress)
    # m8190a_duc_dig_mod_example(ipAddress)
    # m8190a_duc_chirp_example(ipAddress)
    # m8190a_iq_correction_example(ipAddress, '127.0.0.1', '"Analyzer1"')
    # m8195a_simple_wfm_example(ipAddress)
    # vsg_chirp_example(ipAddress)
    # vsg_dig_mod_example(ipAddress)
    # vsg_am_example(ipAddress)
    # vsg_mtone_example(ipAddress)
    # vector_uxg_dig_mod_example(ipAddress)
    # vector_uxg_pdw_example(ipAddress)
    # vector_uxg_lan_streaming_example(ipAddress)
    # analog_uxg_pdw_example(ipAddress)
    # wfm_to_vsa_example(ipAddress)
    # vsa_vector_example(ipAddress)
    vxg_mat_import_example(ipAddress, fileName=matFilePath)
    # gui_example()


if __name__ == '__main__':
    main()
