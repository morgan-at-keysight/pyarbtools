"""
Simple Waveform Download for Keysight AWGs
Author: Morgan Allison
Updated: 06/18
Creates a simple waveform, transfers it to the M8195A, and begin playback.
Uses pySource.py for instrument communication
Python 3.6.4
PyVISA 1.9.0
NumPy 1.14.2
Tested on M8195A
"""

import numpy as np
from pySource import *


def main():
    """Simple waveform download example."""
    # Create M8190A instrument object
    awg = M8195A('141.121.210.205', reset=True)
    awg.sanity_check()

    # User-defined sample rate and sine frequency.
    ############################################################################
    fs = 64e9
    cf = 1e9
    dacMode = 'single'
    func = 'arb'
    ############################################################################

    awg.configure(dacMode=dacMode, fs=fs, func=func)

    # Configure signal amplitude.
    amp = 0.5
    offset = 0
    awg.write(f'volt:ampl {amp}')
    ampRead = float(awg.query('volt:ampl?').strip())
    awg.write(f'volt:offs {offset}')
    offsetRead = float(awg.query('volt:offs?').strip())
    print(f'Amplitude: {ampRead} V, Offset: {offsetRead} V')

    # Define a waveform.
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


if __name__ == '__main__':
    main()
