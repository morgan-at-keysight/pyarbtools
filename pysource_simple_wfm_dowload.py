"""
Simple Waveform Download for Keysight AWGs
Author: Morgan Allison
Updated: 06/18
Creates a simple waveform, transfers it to the M8190A, and begin playback.
Uses pySource.py for instrument communication
Python 3.6.4
PyVISA 1.9.0
NumPy 1.14.2
Tested on M8190A
"""

import numpy as np
from pySource import *


def main():
    """Simple waveform download example."""
    # Create M8190A instrument object
    awg = M8190A('141.121.210.240', reset=True)

    # User-defined sample rate and sine frequency.
    ############################################################################
    fs = 10e9
    cf = 1e9
    res = 'wsp'
    out1 = 'dac'
    func1 = 'arb'
    ############################################################################

    awg.configure(res=res, fs=fs, out1=out1, func1=func1)

    # Configure DC offset and signal amplitude.
    offset = 0
    amp = 0.5
    awg.write(f'dac:volt:ampl {amp}')
    ampRead = float(awg.query('dac:volt:ampl?').strip())
    awg.write(f'dac:volt:offs {offset}')
    offsetRead = float(awg.query('dac:volt:offs?').strip())
    print(f'Amplitude: {ampRead} V, Offset: {offsetRead} V')

    # Define a waveform.
    rl = fs / cf * awg.gran
    t = np.linspace(0, rl / fs, rl, endpoint=False)
    wfm = awg.check_wfm(np.sin(2 * np.pi * cf * t))

    # Define segment 1 and populate it with waveform data.
    awg.download_wfm(wfm)

    # Assign segment 1 to trace (channel) 1 and start continuous playback.
    awg.write('trace:select 1')
    awg.write('output1:norm on')
    awg.write('init:cont on')
    awg.write('init:imm')
    awg.query('*opc?')

    # Check for errors and gracefully disconnect.
    awg.err_check()
    awg.disconnect()


if __name__ == '__main__':
    main()
