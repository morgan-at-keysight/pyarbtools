"""
examples
Author: Morgan Allison, Keysight RF/uW Application Engineer
Provides example scripts for generic VSGs, UXG, and AWGs using
instrument classes from pyarbtools.
Tested on N5182B, M8190A
"""

import pyarbtools
import numpy as np
import csv


def vsg_chirp_example(ipAddress):
    """Creates downloads, assigns, and plays out a chirp waveform with
    a generic VSG."""

    vsg = pyarbtools.instruments.VSG(ipAddress, port=5025, reset=True)
    vsg.configure(amp=-20, fs=50e6, cf=1e9)
    vsg.clear_all_wfm()
    vsg.sanity_check()

    name = 'chirp'
    pWidth = 10e-6
    bw = 40e6
    pri = 100e-6
    iq = pyarbtools.wfmBuilder.chirp_generator(fs=vsg.fs, pWidth=pWidth, pri=pri, chirpBw=bw)

    vsg.download_wfm(iq, name)
    vsg.play(name)
    vsg.err_check()
    vsg.disconnect()


def vsg_dig_mod_example(ipAddress):
    """Generates and plays 1 MHz 16 QAM signal with 0.35 alpha RRC filter
    @ 1 GHz CF with a generic VSG."""

    vsg = pyarbtools.instruments.VSG(ipAddress, port=5025, timeout=15, reset=True)
    vsg.configure(amp=-5, fs=100e6)
    vsg.sanity_check()
    vsg.err_check()

    name = '1GHz_16QAM'
    symRate = 200e6
    iq = pyarbtools.wfmBuilder.digmod_prbs_generator(fs=2.56e9, modType='qam16',symRate=symRate, prbsOrder=15)

    fileName = 'C:\\users\\moalliso\\Desktop\\200MHz_16QAM.csv'
    with open(fileName, 'w', newline='\n') as f:
        w = csv.writer(f)
        for sample in iq:
            w.writerow([str(sample.real), str(sample.imag)])

    vsg.clear_all_wfm()
    vsg.download_wfm(iq, wfmID=name)
    vsg.play(name)
    vsg.err_check()
    vsg.disconnect()


def vsg_am_example(ipAddress):
    """Generates an AM tone with the IQ modulator in a generic VSG."""
    amRate = 100e3
    amDepth = 75
    fs = 100e6

    vsg = pyarbtools.instruments.VSG(ipAddress, reset=True)
    vsg.configure(cf=1e9, amp=0, fs=fs, iqScale=70, refSrc='int')

    iq = pyarbtools.wfmBuilder.am_generator(fs=fs, amDepth=amDepth, modRate=amRate)

    vsg.download_wfm(iq, wfmID='custom_am')
    vsg.play('custom_am')

    vsg.err_check()
    vsg.disconnect()


def vsg_mtone_example(ipAddress):
    """Generates a mutlitone signal on a generic VSG."""
    numTones = 41
    toneSpacing = 750e3
    fs = 100e6

    vsg = pyarbtools.instruments.VSG(ipAddress, reset=True)
    vsg.configure(cf=1e9, amp=0, fs=fs, refSrc='int')

    iq = pyarbtools.wfmBuilder.multitone(fs=fs, spacing=toneSpacing, num=numTones)

    vsg.download_wfm(iq, wfmID='mtone')
    vsg.play('mtone')

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
    iq = pyarbtools.wfmBuilder.digmod_prbs_generator(fs=awg.bbfs, modType=modType, symRate=symRate, wfmFormat='iq')

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


def m8190a_iq_correction_example(instIPAddress, vsaIPAddress, vsaHardware):
    """Performs IQ calibration on a digitally modulated signal using VSA."""

    awg = pyarbtools.instruments.M8190A(instIPAddress, reset=True)
    awg.configure('intx3', fs=7.2e9, out1='ac', cf1=1e9)

    iq = pyarbtools.wfmBuilder.digmod_prbs_generator(fs=awg.bbfs, modType='qam32', symRate=40e6)
    iqCorr = pyarbtools.wfmBuilder.iq_correction(iq, awg, vsaIPAddress, vsaHardware=vsaHardware, osFactor=20, convergence=5e-9)

    wfmID = awg.download_wfm(iqCorr)
    awg.play(wfmID=wfmID)
    awg.err_check()
    awg.disconnect()


def m8195a_simple_wfm_example(ipAddress):
    """Sets up the M8195A and creates, downloads, assigns, and plays
    out a simple sine waveform from the AC output port."""

    dacMode = 'dual'
    fs = 64e9
    refSrc = 'ext'
    refFreq = 200e6
    cf = 1e9
    wfmName = 'sine'

    awg = pyarbtools.instruments.M8195A(ipAddress, reset=True)
    awg.configure(dacMode=dacMode, fs=fs, refSrc=refSrc, refFreq=refFreq)

    # Define a waveform, ensuring min length and granularity requirements are met
    real = pyarbtools.wfmBuilder.sine_generator(fs=fs, freq=cf, wfmFormat='real')

    # Define segment 1 and populate it with waveform data.
    segment = awg.download_wfm(real, ch=1, name=wfmName)

    # Assign segment to channel 1 and start playback.
    awg.play(wfmID=segment, ch=1)

    # Check for errors and gracefully disconnect.
    awg.err_check()
    awg.disconnect()


def vector_uxg_arb_example(ipAddress):
    """Generates and plays 10 MHz 64 QAM signal with 0.35 alpha RRC filter
    @ 1 GHz CF with vector UXG."""

    cf = 1e9
    modType = 'qam16'
    symRate = 10e6
    wfmName = '10M_16QAM'

    uxg = pyarbtools.instruments.VectorUXG(ipAddress, port=5025, timeout=10, reset=True)
    uxg.configure(rfState=1, cf=cf, amp=-20)

    iq = pyarbtools.wfmBuilder.digmod_prbs_generator(fs=uxg.fs, modType=modType, symRate=symRate)

    uxg.download_wfm(iq, wfmID=wfmName)
    uxg.play(wfmID=wfmName)

    uxg.err_check()
    uxg.disconnect()


def vector_uxg_pdw_example(ipAddress):
    """Creates and downloads a chirp waveform, defines a simple pdw csv
    file, and loads that pdw file into the UXG, and plays it out."""

    pWidth = 10e-6
    chirpBw = 40e6
    wfmName = 'CHIRP'

    uxg = pyarbtools.instruments.VectorUXG(ipAddress, port=5025, timeout=10, reset=True)
    uxg.configure()

    """Configure pdw markers. These commands will assign a TTL pulse 
    at the beginning of each PDW. The trigger 2 output will only be 
    active if the Marker field for a given PDW is specified as '0x1'"""
    uxg.write('stream:markers:pdw1:mode stime')
    uxg.write('route:trigger2:output pmarker1')

    # Create and download chirp waveform
    iq = pyarbtools.wfmBuilder.chirp_generator(fs=uxg.fs, pWidth=pWidth, pri=pWidth, chirpBw=chirpBw, zeroLast=True)
    uxg.download_wfm(iq, wfmName)

    # Define and generate csv pdw file
    pdwName = 'basic_chirp'
    fields = ['Operation', 'Time', 'Frequency', 'Zero/Hold', 'Markers', 'Name',]
    data = ([1, 0, 1e9, 'Hold', '0x1', wfmName],
            [2, 10e-6, 1e9, 'Hold', '0x0', wfmName])

    uxg.csv_pdw_file_download(pdwName, fields, data)

    uxg.stream_start(pdwID=pdwName)

    uxg.err_check()
    uxg.disconnect()


def vector_uxg_lan_streaming_example(ipAddress):
    """Creates and downloads iq waveforms & a waveform index file,
    builds a PDW file, configures LAN streaming, and streams the PDWs
    to the UXG."""

    uxg = pyarbtools.instruments.VectorUXG(ipAddress, port=5025, timeout=10, reset=True)
    uxg.configure(rfState=1, modState=1)
    uxg.clear_all_wfm()

    # Waveform creation, three chirps of the same bandwidth and different lengths
    lengths = [10e-6, 50e-6, 100e-6]
    wfmNames = []
    for l in lengths:
        iq = pyarbtools.wfmBuilder.chirp_generator(fs=uxg.fs, pWidth=l, pri=l, chirpBw=100e6, wfmFormat='iq', zeroLast=True)
        uxg.download_wfm(iq, f'{l}_100MHz_CHIRP')
        wfmNames.append(f'{l}_100MHz_CHIRP')

    # Create/download waveform index file
    windex = {'fileName': 'chirps', 'wfmNames': wfmNames}
    uxg.csv_windex_file_download(windex)

    # Create PDWs
    # operation, freq, phase, startTimeSec, power, markers,
    # phaseControl, rfOff, wIndex, wfmMkrMask

    rawPdw = [[1, 1e9, 0, 0,      -10, 0, 0, 0, 0, 0xF],
              [0, 1e9, 0, 20e-6,  -10, 0, 0, 0, 1, 0xF],
              [0, 1e9, 0, 120e-6, -10, 0, 0, 0, 2, 0xF],
              [2, 1e9, 0, 300e-6, -10, 0, 0, 0, 2, 0xF]]

    pdwFile = uxg.bin_pdw_file_builder(rawPdw)

    # Separate pdwFile into header and data portions
    header = pdwFile[:4096]
    data = pdwFile[4096:]

    uxg.write('stream:source lan')
    uxg.write('stream:trigger:play:file:type continuous')
    uxg.write('stream:trigger:play:file:type:continuous:type trigger')
    uxg.write('stream:trigger:play:source bus')
    uxg.write(f'memory:import:windex "{windex["fileName"]}.csv","{windex["fileName"]}"')
    uxg.write(f'stream:windex:select "{windex["fileName"]}"')

    uxg.write('stream:external:header:clear')

    # The esr=False argument in binblockwrite() allows you to send your own
    # read/query after writing the binary block data rather than the
    # default *ESR? query that is used for error checking.
    uxg.binblockwrite(f'stream:external:header? ', header, esr=False)
    if uxg.query('') != '+0':
        raise pyarbtools.error.VSGError('stream:external:header? response invalid. This should never happen.')

    # Configure LAN streaming and send PDWs
    # uxg.write('stream:state on')
    uxg.open_lan_stream()
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

    uxg = pyarbtools.instruments.AnalogUXG(ipAddress, port=5025, timeout=10, reset=False)
    uxg.configure(rfState=0, modState=1, cf=1e9, amp=0)
    uxg.err_check()

    # Define and generate binary pdw file
    # operation, freq, phase, startTimeSec, width, power, markers,
    # pulseMode, phaseControl bandAdjust, chirpControl, code,
    # chirpRate, freqMap
    pdwName = 'analog'
    pdwList = [[1, 980e6, 0, 0, 10e-6, 1, 0, 2, 0, 0, 3, 0, 4000000, 0],
               [2, 1e9, 0, 20e-6, 1e-6, 1, 0, 2, 0, 0, 0, 0, 0, 0]]
    pdwFile = uxg.bin_pdw_file_builder(pdwList)
    uxg.download_bin_pdw_file(pdwFile, pdwName=pdwName)
    uxg.err_check()

    uxg.stream_play(pdwID=pdwName)
    uxg.disconnect()


def main():
    """Uncomment the example you'd like to run. For each example,
    replace the IP address with one that is appropriate for your
    instrument(s)."""

    # m8190a_simple_wfm_example('141.121.210.171')
    # m8190a_duc_dig_mod_example('141.121.210.171')
    # m8190a_duc_chirp_example('141.121.210.171')
    # m8190a_iq_correction_example('141.121.210.171', '127.0.0.1', '"Analyzer1"')
    # m8195a_simple_wfm_example('141.121.210.245')
    vsg_dig_mod_example('192.168.50.124')
    # vsg_chirp_example('192.168.50.124')
    # vsg_am_example('192.168.50.124')
    # vsg_mtone_example('192.168.50.124')
    # vector_uxg_arb_example('141.121.210.131')
    # vector_uxg_pdw_example('141.121.210.131')
    # vector_uxg_lan_streaming_example('141.121.210.131')
    # analog_uxg_pdw_example('141.121.231.135')


if __name__ == '__main__':
    main()
