"""
examples
Author: Morgan Allison, Keysight RF/uW Application Engineer
Provides example scripts for generic VSGs, and AWGs using
instrument classes from PyArbTools.
"""

import pyarbtools


def vsg_chirp_example(ipAddress):
    """Creates downloads, assigns, and plays out a chirp waveform with
    a generic VSG."""

    # Create VSG object
    vsg = pyarbtools.instruments.VSG(ipAddress, apiType='pyvisa', protocol='hislip', port=0, timeout=3, reset=True)
    # vsg = pyarbtools.instruments.VSG(ipAddress, port=5025, timeout=15, reset=True)

    # Signal generator configuration variables
    amplitude = -5
    sampleRate = 50e6
    freq = 1e9

    # Configure signal generator
    vsg.configure(amp=amplitude, fs=sampleRate, cf=freq)
    vsg.sanity_check()

    # Waveform definition variables
    name = "chirp"
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
    vsg.close()


def vsg_dig_mod_example(ipAddress):
    """Generates and plays 1 MHz 16 QAM signal with 0.35 alpha RRC filter
    @ 1 GHz CF with a generic VSG."""

    # Create VSG object
    vsg = pyarbtools.instruments.VSG(ipAddress, apiType='pyvisa', protocol='hislip', port=0, timeout=3, reset=True)
    # vsg = pyarbtools.instruments.VSG(ipAddress, port=5025, timeout=15, reset=True)

    # Signal generator configuration variables
    amplitude = -5
    sampleRate = 200e6
    freq = 1e9

    # Configure signal generator
    vsg.configure(amp=amplitude, fs=sampleRate, cf=freq, iqScale=70)
    vsg.sanity_check()
    vsg.err_check()

    # Waveform definition variables
    name = "10MHZ_16QAM"
    symRate = 10e6
    modType = "qam16"

    # Create waveform
    iq = pyarbtools.wfmBuilder.digmod_generator(fs=vsg.fs, modType=modType, symRate=symRate, filt="rootraisedcosine")

    # Download and play waveform
    vsg.download_wfm(iq, wfmID=name)
    vsg.play(name)

    # Check for errors and gracefully disconnect
    vsg.err_check()
    vsg.close()


def vsg_am_example(ipAddress):
    """Generates an AM tone with the IQ modulator in a generic VSG."""

    # Create VSG object
    vsg = pyarbtools.instruments.VSG(ipAddress, apiType='pyvisa', protocol='hislip', port=0, timeout=3, reset=True)
    # vsg = pyarbtools.instruments.VSG(ipAddress, port=5025, timeout=15, reset=True)

    # Signal generator configuration variables
    amplitude = -5
    sampleRate = 100e6
    freq = 1e9

    # Configure signal generator
    vsg.configure(amp=amplitude, fs=sampleRate, cf=freq)
    vsg.sanity_check()
    vsg.err_check()

    # Waveform definition variables
    name = "CUSTOM_AM"
    amRate = 100e3
    amDepth = 75

    # Create waveform
    iq = pyarbtools.wfmBuilder.am_generator(fs=vsg.fs, amDepth=amDepth, modRate=amRate)

    # Download and play waveform
    vsg.download_wfm(iq, wfmID=name)
    vsg.play(name)

    # Check for errors and gracefully disconnect
    vsg.err_check()
    vsg.close()


def vsg_mtone_example(ipAddress):
    """Generates a mutlitone signal on a generic VSG."""

    vsg = pyarbtools.instruments.VSG(ipAddress, apiType='pyvisa', protocol='hislip', port=0, timeout=3, reset=True)
    # vsg = pyarbtools.instruments.VSG(ipAddress, port=5025, timeout=15, reset=True)

    # Signal generator configuration variables
    amplitude = -5
    sampleRate = 100e6
    freq = 1e9

    # Configure signal generator
    vsg.configure(amp=amplitude, fs=sampleRate, cf=freq)
    vsg.sanity_check()
    vsg.err_check()

    # Waveform definition variables
    name = "MULTITONE"
    numTones = 400
    toneSpacing = 100e3

    # Create waveform
    iq = pyarbtools.wfmBuilder.multitone_generator(fs=vsg.fs, spacing=toneSpacing, num=numTones)

    # Download and play waveform
    vsg.download_wfm(iq, wfmID=name)
    vsg.play(name)

    # Check for errors and gracefully disconnect
    vsg.err_check()
    vsg.close()


def m8190a_simple_wfm_example(ipAddress):
    """Sets up the M8190A and creates, downloads, assigns, and plays
    out a simple sine waveform from the AC output port."""

    res = "wsp"
    fs = 10e9
    output = "ac"
    amp = 0.6
    cf = 1e9
    wfmName = "sine"

    awg = pyarbtools.instruments.M8190A(ipAddress, apiType='pyvisa', protocol='hislip', port=0, timeout=3, reset=True)
    # awg = pyarbtools.instruments.M8190A(ipAddress, port=5025, timeout=15, reset=True)
    awg.configure(res=res, fs=fs, out1=output, amp1=amp)

    # Create simple sinusoidal waveform
    real = pyarbtools.wfmBuilder.sine_generator(fs=awg.fs, freq=cf, wfmFormat="real")

    # Define segment 1 and populate it with waveform data.
    segment = awg.download_wfm(real, ch=1, name=wfmName, wfmFormat="real")

    # Assign segment to channel 1 and start playback.
    awg.play(ch=1, wfmID=segment)

    # Check for errors and gracefully disconnect.
    awg.err_check()
    awg.close()


def m8190a_duc_dig_mod_example(ipAddress):
    """Creates a 10 MHz 16 QAM waveform using digital upconversion on the M8190A."""

    res = "intx3"
    cf = 1e9
    output = "ac"

    modType = "qam16"
    symRate = 10e6
    wfmName = "10MHz_16QAM"

    awg = pyarbtools.instruments.M8190A(ipAddress, apiType='pyvisa', protocol='hislip', port=0, timeout=3, reset=True)
    # awg = pyarbtools.instruments.M8190A(ipAddress, port=5025, timeout=15, reset=True)
    awg.configure(res=res, cf1=cf, out1=output)

    # Create 16 QAM signal.
    iq = pyarbtools.wfmBuilder.digmod_generator(fs=awg.bbfs, modType=modType, symRate=symRate, filt="rootraisedcosine")

    # Download waveform to memory
    segment = awg.download_wfm(iq, ch=1, name=wfmName, wfmFormat="iq")

    # Assign segment to channel 1 and start playback
    awg.play(wfmID=segment, ch=1)
    awg.err_check()
    awg.close()


def m8190a_duc_chirp_example(ipAddress):
    """Creates a 40 MHz chirped pulse using digital upconversion on the M8190A."""

    wfmName = "chirp"
    res = "intx3"
    fs = 7.2e9
    output = "ac"
    cf = 1e9

    pw = 10e-6
    pri = 100e-6
    bw = 40e6

    awg = pyarbtools.instruments.M8190A(ipAddress, apiType='pyvisa', protocol='hislip', port=0, timeout=3, reset=True)
    # awg = pyarbtools.instruments.M8190A(ipAddress, port=5025, timeout=15, reset=True)
    
    awg.configure(res=res, fs=fs, out1=output, cf1=cf)

    # Create chirp waveform.
    iq = pyarbtools.wfmBuilder.chirp_generator(fs=awg.bbfs, pWidth=pw, pri=pri, chirpBw=bw, wfmFormat="iq")

    # Interleave i and q into a single waveform and download to segment 1.
    segment = awg.download_wfm(iq, ch=1, name=wfmName, wfmFormat="iq")

    # Assign segment to channel 1 and start playback.
    awg.play(wfmID=segment, ch=1)

    # Check for errors and gracefully disconnect.
    awg.err_check()
    awg.close()


def m8195a_simple_wfm_example(ipAddress):
    """Sets up the M8195A and creates, downloads, assigns, and plays
    out a simple sine waveform from the AC output port."""

    # Create M8195A object
    awg = pyarbtools.instruments.M8195A(ipAddress, apiType='pyvisa', protocol='hislip', port=0, timeout=3, reset=True)
    # awg = pyarbtools.instruments.M8195A(ipAddress, port=5025, timeout=15, reset=True)

    # AWG configuration variables
    dacMode = "dual"
    fs = 64e9
    awg.configure(dacMode=dacMode, fs=fs, amp1=100e-3)

    # Waveform definition variables
    sineFreq = 1e9
    wfmFormat = "real"

    # Define a waveform, ensuring min length and granularity requirements are met
    real = pyarbtools.wfmBuilder.sine_generator(fs=awg.fs, freq=sineFreq, wfmFormat=wfmFormat)

    # Download waveform to AWG and get waveform identifier
    wfmID = awg.download_wfm(real, ch=1)

    # Play waveform using identifier
    awg.play(wfmID=wfmID, ch=1)

    # Check for errors and gracefully disconnect.
    awg.err_check()
    awg.close()


def m8190a_sequence_example(ipAddress):
    """Creates a simple sinusoidal waveform and uses the idle segment in the sequencer to make it a pulsed signal."""

    # AWG Settings
    fs = 12e9
    res = "wsp"
    out1 = "dac"
    amp1 = 0.7
    func1 = "sts"

    # Waveform Settings
    cf = 1e9
    pulseOffTime = 1e-6

    # Connect to AWG and configure settings.
    awg = pyarbtools.instruments.M8190A(ipAddress, apiType='pyvisa', protocol='hislip', port=0, timeout=3, reset=True)
    # awg = pyarbtools.instruments.M8190A(ipAddress, port=5025, timeout=15, reset=True)

    awg.configure(res=res, fs=fs, out1=out1, amp1=amp1, func1=func1)

    # Create a simple sine wave at our desired carrier frequency.
    sineWfmData = pyarbtools.wfmBuilder.sine_generator(fs=awg.fs, freq=cf, wfmFormat="real")
    sineWfmID = awg.download_wfm(sineWfmData, name="sine", wfmFormat="real")

    # We have to create an "endcap" waveform because the sequence cannot end with an idle segment.
    zeroWfmData = pyarbtools.wfmBuilder.zero_generator(fs=awg.fs, numSamples=awg.minLen, wfmFormat="real")
    zeroWfmID = awg.download_wfm(zeroWfmData, name="zero", wfmFormat="real")

    # Calculate how many samples to delay in the idle segment, taking into account the length of the "endcap" waveform.
    idleDelay = int(pulseOffTime * awg.fs - len(zeroWfmData))

    # Build our sequence
    awg.create_sequence(3)
    awg.insert_wfm_in_sequence(sineWfmID, 0, seqStart=True)
    awg.insert_idle_in_sequence(1, idleDelay=idleDelay)
    awg.insert_wfm_in_sequence(zeroWfmID, 2, seqEnd=True)

    # Play the sequence
    awg.play_sequence()

    awg.close()


def wfm_to_vsa_example(ipAddress):
    """This function creates a "perfect" digitally modulated waveform, exports it to a csv file,
    recalls it into VSA, and configures VSA to analyze it."""

    # Waveform creation variables
    symRate = 10e6
    fs = 100e6
    modType = "qam256"
    psFilter = "rootraisedcosine"
    alpha = 0.35
    fileName = "C:\\Temp\\wfm.csv"
    fileFormat = "csv"

    print("Creating waveform.")
    # This is the new digital modulation waveform creation function
    data = pyarbtools.wfmBuilder.digmod_generator(
        fs=fs,
        symRate=symRate,
        modType=modType,
        filt=psFilter,
        numSymbols=10000,
        alpha=alpha,
    )

    print("Exporting waveform.")
    # Export the waveform to a csv file
    pyarbtools.wfmBuilder.export_wfm(data, fileName, True, fs)

    print("Setting up VSA.")
    # Create VSA object
    vsa = pyarbtools.vsaControl.VSA(ipAddress, vsaHardware=None, timeout=10, reset=False)

    # Select a digital demod measurement and configure it to measure the saved waveform
    vsa.set_measurement("ddemod")
    if psFilter.lower() == "rootraisedcosine":
        mFilter = "rootraisedcosine"
        rFilter = "raisedcosine"
    elif psFilter.lower() == "raisedcosine":
        mFilter = "none"
        rFilter = "raisedcosine"
    else:
        raise Exception("Invalid filter type chosen.")

    # Configure digital demodulation in VSA
    vsa.configure_ddemod(
        amp=0,
        modType=modType,
        symRate=symRate,
        measFilter=mFilter,
        refFilter=rFilter,
        filterAlpha=alpha,
        measLength=1000,
        eqState=False,
    )

    # Recall csv file we exported earlier
    vsa.recall_recording(fileName, fileFormat=fileFormat)

    # Perform a single-shot replay in VSA
    vsa.acquire_single()

    # Check for errors and gracefully disconnect
    vsa.err_check()
    vsa.close()


def vsa_vector_example(ipAddress):
    """Connects to a running instance of VSA, configures a vector measurement, and prints out settings."""

    # Vector configuration settings
    cf = 1e9
    span = 20e6
    amp = -5
    time = 100e-6

    vsa = pyarbtools.vsaControl.VSA(ipAddress)
    vsa.set_measurement("vector")
    vsa.configure_vector(cf=cf, span=span, amp=amp, time=time)
    vsa.acquire_single()
    vsa.sanity_check()

    # Check for errors and gracefully disconnect
    vsa.err_check()
    vsa.close()


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
    wfmDict = pyarbtools.wfmBuilder.import_mat(fileName, targetVariable="iqdata")

    # Create VXG object
    vxg = pyarbtools.instruments.VXG(ipAddress, apiType='pyvisa', protocol='hislip', port=1, timeout=3, reset=True)
    # vxg = pyarbtools.instruments.VXG(ipAddress, port=5025, timeout=15, reset=True)

    # Configure vxg based on variables imported from the .mat file
    vxg.configure(cf2=1e9, fs2=wfmDict["fs"], rfState2=1, amp2=0)

    # Download waveform to vxg by passing the complex array of samples and the waveform name from the dict
    vxg.download_wfm(wfmDict["data"], wfmID=wfmDict["wfmID"])

    # Play out the waveform by referencing the waveform name from the dict
    vxg.play(wfmID=wfmDict["wfmID"], ch=2)

    vxg.close()


def vxg_dig_mod_example(ipAddress):
    """Generates and plays 1 MHz 16 QAM signal with 0.35 alpha RRC filter
    @ 1 GHz CF with a generic VSG."""

    # Create VSG object
    vxg = pyarbtools.instruments.VXG(ipAddress, apiType='pyvisa', protocol='socket', port=5025, timeout=3, reset=True)
    # vxg = pyarbtools.instruments.VXG(ipAddress, port=5025, timeout=15, reset=True)

    # Signal generator configuration variables
    amplitude = -5
    sampleRate = 200e6
    freq = 1e9

    # Configure signal generator
    vxg.configure(amp1=amplitude, fs1=sampleRate, cf1=freq, iqScale1=70)
    vxg.sanity_check()
    vxg.err_check()

    # Waveform definition variables
    name = "100MHZ_16QAM"
    symRate = 100e6
    modType = "qam16"

    # Create waveform
    iq = pyarbtools.wfmBuilder.digmod_generator(fs=vxg.fs1, modType=modType, symRate=symRate, filt="rootraisedcosine")

    # Download and play waveform
    vxg.download_wfm(iq, wfmID=name)
    vxg.play(name)

    # Check for errors and gracefully disconnect
    vxg.err_check()
    vxg.close()


def gui_example():
    """Starts experimental PyArbTools GUI"""
    pyarbtools.gui.main()


def main():
    """Uncomment the example you'd like to run. For each example,
    replace the IP address with one that is appropriate for your
    instrument(s)."""
    ipAddress = "192.168.4.68"
    matFilePath = "<insert path to .mat file here>"

    # m8190a_simple_wfm_example(ipAddress)
    # m8190a_duc_dig_mod_example(ipAddress)
    # m8190a_duc_chirp_example(ipAddress)
    # m8190a_iq_correction_example(ipAddress, '127.0.0.1', '"Analyzer1"')
    # m8195a_simple_wfm_example(ipAddress)
    # vsg_chirp_example(ipAddress)
    # vsg_dig_mod_example(ipAddress)
    # vsg_am_example(ipAddress)
    # vsg_mtone_example(ipAddress)
    # wfm_to_vsa_example(ipAddress)
    # vsa_vector_example(ipAddress)
    # vxg_mat_import_example(ipAddress, fileName=matFilePath)
    vxg_dig_mod_example(ipAddress)
    # m8190a_sequence_example(ipAddress)
    # gui_example()


if __name__ == "__main__":
    main()
