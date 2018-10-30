"""
Example Functions for pyarbtools
Author: Morgan Allison, Keysight RF/uW Application Engineer
Updated: 10/18
Provides example scripts for generic VSGs, UXG, and AWGs using
instrument classes from pyarbtools.
Python 3.6.4
NumPy 1.14.2
Tested on N5182B, M8190A
"""

import pyarbtools
import numpy as np


def vsg_chirp_example(ipAddress):
    """Creates downloads, assigns, and plays out a chirp waveform with
    a generic VSG."""

    vsg = pyarbtools.instruments.VSG(ipAddress, port=5025, reset=True)
    vsg.configure(amp=-20, fs=50e6, iqScale=70)
    vsg.sanity_check()

    name = 'chirp'
    length = 100e-6
    bw = 40e6
    i, q = pyarbtools.wfmBuilder.chirp_generator(length=length, fs=vsg.fs, chirpBw=bw)

    i = np.append(i, np.zeros(5000))
    q = np.append(q, np.zeros(5000))
    vsg.write('mmemory:delete:wfm')
    vsg.download_iq_wfm(i, q, name)
    vsg.play(name)
    vsg.err_check()
    vsg.disconnect()


def vsg_dig_mod_example(ipAddress):
    """Generates and plays 1 MHz 16 QAM signal with 0.35 alpha RRC filter
    @ 1 GHz CF with a generic VSG."""

    vsg = pyarbtools.instruments.VSG(ipAddress, port=5025, timeout=15, reset=True)
    vsg.configure(amp=-5, fs=50e6, iqScale=70)
    vsg.sanity_check()

    name = '1MHZ_16QAM'
    symRate = 1e6
    i, q = pyarbtools.wfmBuilder.digmod_prbs_generator('qam16', vsg.fs, symRate)

    vsg.write('mmemory:delete:wfm')
    vsg.download_iq_wfm(i, q, name)
    vsg.play(name)
    vsg.err_check()
    vsg.disconnect()


def m8190a_simple_wfm_example(ipAddress):
    """Sets up the M8190A and creates, downloads, assigns, and plays
    out a simple sine waveform from the AC output port."""

    # User-defined sample rate and sine frequency.
    ############################################################################
    fs = 10e9
    cf = 1e9
    res = 'wsp'
    out1 = 'ac'
    ############################################################################

    awg = pyarbtools.instruments.M8190A(ipAddress, reset=True)
    awg.configure(res=res, fs=fs, out1=out1)

    # Define a waveform, ensuring min length and granularity requirements are met
    rl = fs / cf * awg.gran
    t = np.linspace(0, rl / fs, rl, endpoint=False)
    wfm = awg.check_wfm(np.sin(2 * np.pi * cf * t))

    # Define segment 1 and populate it with waveform data.
    awg.download_wfm(wfm)

    # Assign segment 1 to channel 1 and start continuous playback.
    awg.play(ch=1, wfm=1)

    # Check for errors and gracefully disconnect.
    awg.err_check()
    awg.disconnect()


def m8190a_duc_dig_mod_example(ipAddress):
    """Sets up the digital upconverter on the M8190A and creates,
    downloads, assigns, and plays back a 16 QAM waveform from
    the AC output port."""

    awg = pyarbtools.instruments.M8190A(ipAddress, port=5025, reset=True)
    awg.configure(res='intx3', cf1=1e9, out1='ac')

    # Create 16 QAM signal.
    symRate = 20e6
    i, q = pyarbtools.wfmBuilder.digmod_prbs_generator('qam16', awg.bbfs, symRate)

    # Define segment 1 and populate it with waveform data.
    awg.download_iq_wfm(i, q)

    awg.play(ch=1, wfm=1)
    awg.err_check()
    awg.disconnect()


def m8190a_duc_chirp_example(ipAddress):
    """Creates a chirped pulse using digital upconversion in the M8190."""
    """User-defined sample rate, carrier frequency, chirp bandwidth, 
    pri, pulse width, and resolution."""
    ############################################################################
    name = 'chirp'
    fs = 7.2e9
    cf = 1e9
    bw = 40e6
    pri = 200e-6
    pw = 100e-6
    res = 'intx3'
    ############################################################################

    awg = pyarbtools.instruments.M8190A(ipAddress, reset=True)
    awg.configure(res=res, fs=fs, out1='ac', cf1=cf)
    bbfs = fs / awg.intFactor

    # Create chirp and append dead time to waveform.
    i, q = pyarbtools.wfmBuilder.chirp_generator(pw, bbfs, bw)
    deadTime = np.zeros(int(bbfs * (pri - pw)))
    i = np.append(i, deadTime)
    q = np.append(q, deadTime)

    # Interleave i and q into a single waveform and download to segment 1.
    wfmID = awg.download_iq_wfm(i, q, ch=1, name=name)

    # Assign segment 1 to trace (channel) 1 and start continuous playback.
    awg.play(wfmID=wfmID)

    # Check for errors and gracefully disconnect.
    awg.err_check()
    awg.disconnect()


def m8190a_iq_correction_example(instIPAddress, vsaIPAddress, vsaHardware):
    """Performs IQ calibration on a digitally modulated signal using VSA."""

    awg = pyarbtools.instruments.M8190A(instIPAddress, reset=True)
    awg.configure('intx3', fs=7.2e9, out1='ac', cf1=1e9)

    i, q = pyarbtools.wfmBuilder.digmod_prbs_generator('qam32', awg.bbfs, 40e6)

    iCorr, qCorr = pyarbtools.wfmBuilder.iq_correction(
        i, q, awg, vsaIPAddress, vsaHardware=vsaHardware, osFactor=20)

    wfmID = awg.download_iq_wfm(iCorr, qCorr)
    awg.play(wfmID=wfmID)
    awg.err_check()
    awg.disconnect()


def m8195a_simple_wfm_example(ipAddress):
    """Sets up the M8195A and creates, downloads, assigns, and plays
    out a simple sine waveform from the AC output port."""

    # User-defined sample rate and sine frequency.
    ############################################################################
    fs = 64e9
    cf = 1e9
    dacMode = 'single'
    func = 'arb'
    ############################################################################

    awg = pyarbtools.instruments.M8195A(ipAddress, reset=True)
    awg.configure(dacMode=dacMode, fs=fs, func=func)

    # Define a waveform, ensuring min length and granularity requirements are met
    rl = fs / cf * awg.gran
    t = np.linspace(0, rl / fs, rl, endpoint=False)
    wfm = awg.check_wfm(np.sin(2 * np.pi * cf * t))

    # Define segment 1 and populate it with waveform data.
    awg.download_wfm(wfm)

    # Assign segment 1 to trace (channel) 1 and start continuous playback.
    awg.write('trace:select 1')
    awg.write('output1:state on')
    awg.write('init:cont on')
    awg.write('init:imm')
    awg.query('*opc?')

    # Check for errors and gracefully disconnect.
    awg.err_check()
    awg.disconnect()


def uxg_pdw_example(ipAddress):
    """Creates and downloads a chirp waveform, defines a simple pdw csv
    file, and loads that pdw file into the UXG, and plays it out."""

    """NOTE: trigger settings may need to be adjusted for continuous
    output. This will be fixed in a future release."""

    uxg = pyarbtools.instruments.UXG(ipAddress, port=5025, timeout=10, reset=True)
    uxg.err_check()

    uxg.write('stream:state off')
    uxg.write('radio:arb:state off')

    # Create IQ waveform
    length = 1e-6
    fs = 250e6
    chirpBw = 100e6
    i, q = pyarbtools.wfmBuilder.chirp_generator(length, fs, chirpBw, zeroLast=True)
    wfmName = '1US_100MHz_CHIRP'
    uxg.download_iq_wfm(wfmName, i, q)

    # Define and generate csv pdw file
    pdwName = 'basic_chirp'
    fields = ['Operation', 'Time', 'Frequency', 'Zero/Hold', 'Markers', 'Name']
    data = [[1, 0, 1e9, 'Hold', '0x1', wfmName],
            [2, 10e-6, 1e9, 'Hold', '0x0', wfmName]]

    uxg.csv_pdw_file_download(pdwName, fields, data)
    uxg.write('stream:state on')
    uxg.write('stream:trigger:play:immediate')
    uxg.err_check()
    uxg.disconnect()


def uxg_lan_streaming_example(ipAddress):
    """Creates and downloads iq waveforms & a waveform index file,
    builds a PDW file, configures LAN streaming, and streams the PDWs
    to the UXG."""

    uxg = pyarbtools.instruments.UXG(ipAddress, port=5025, timeout=10, reset=True)
    uxg.err_check()

    # Waveform creation, three chirps of the same bandwidth and different lengths
    lengths = [10e-6, 50e-6, 100e-6]
    wfmNames = []
    for l in lengths:
        i, q = pyarbtools.wfmBuilder.chirp_generator(l, fs=250e6, chirpBw=100e6, zeroLast=True)
        uxg.download_iq_wfm(f'{l}_100MHz_CHIRP', i, q)
        wfmNames.append(f'{l}_100MHz_CHIRP')

    # Create/download waveform index file
    windex = {'fileName': 'chirps', 'wfmNames': wfmNames}
    uxg.csv_windex_file_download(windex)

    # Create PDWs
    # operation, freq, phase, startTimeSec, power, markers,
    # phaseControl, rfOff, wIndex, wfmMkrMask
    rawPdw = [[1, 1e9, 0, 0,      0, 1, 0, 0, 0, 0xF],
              [0, 1e9, 0, 20e-6, 0, 0, 0, 0, 1, 0xF],
              [0, 1e9, 0, 120e-6, 0, 0, 0, 0, 2, 0xF],
              [2, 1e9, 0, 300e-6, 0, 0, 0, 0, 2, 0xF]]

    pdwFile = uxg.bin_pdw_file_builder(rawPdw)

    # Separate pdwFile into header and data portions
    header = pdwFile[:4096]
    data = pdwFile[4096:]

    uxg.write('stream:markers:pdw1:mode stime')
    uxg.write('rout:trigger2:output pmarker1')
    uxg.write('stream:source lan')
    uxg.write('stream:trigger:play:file:type continuous')
    uxg.write('stream:trigger:play:file:type:continuous:type trigger')
    uxg.write('stream:trigger:play:source bus')
    uxg.write(f'memory:import:windex "{windex["fileName"]}.csv","{windex["fileName"]}"')
    uxg.write(f'stream:windex:select "{windex["fileName"]}"')

    uxg.write('stream:external:header:clear')

    # The esr=False argument allows you to send your own read/query after binblockwrite
    uxg.binblockwrite(f'stream:external:header? ', header, esr=False)
    if uxg.query('') != '+0':
        raise pyarbtools.error.VSGError('stream:external:header? response invalid. This should never happen.')

    # Configure LAN streaming and send PDWs
    uxg.write('stream:state on')
    uxg.open_lan_stream()
    uxg.lanStream.send(data)

    # Ensure everything is synchronized
    uxg.query('*opc?')

    # Begin streaming
    uxg.write('stream:trigger:play:immediate')

    # Waiting for stream to finish, turn off stream, close stream port
    uxg.query('*opc?')
    uxg.write('stream:state off')
    uxg.close_lan_stream()

    # Check for errors and gracefully disconnect.
    uxg.err_check()
    uxg.disconnect()


def main():
    # m8190a_duc_dig_mod_example('141.121.210.241')
    # m8190a_duc_chirp_example('141.121.210.241')
    # m8190a_simple_wfm_example('141.121.210.241')
    m8190a_iq_correction_example('141.121.210.241', '127.0.0.1', '"PXA"')
    # m8195a_simple_wfm_example('141.121.210.245')
    # vsg_dig_mod_example('10.112.180.215')
    # vsg_chirp_example('10.112.180.215')
    # uxg_example('141.121.210.167')
    # uxg_lan_streaming_example('141.121.210.167')


if __name__ == '__main__':
    main()
