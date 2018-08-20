"""
Digital Upconverter Simple Waveform Download for M8190 using pySource
Author: Morgan Allison
Updated: 06/18
Creates a simple sine wave using digital upconversion in the M8190.
Uses pySource.py for instrument communication.
Python 3.6.4
NumPy 1.14.2
Tested on M8190A
"""

import numpy as np
from pySource import *


def main():
    """Creates a simple sine wave using digital upconversion in the M8190."""
    awg = M8190A('141.121.210.240', reset=True)

    # User-defined sample rate, carrier frequency, resolution, and function.
    ############################################################################
    fs = 7.2e9
    cf = 100e6
    res = 'intx3'
    func1 = 'arb'
    ############################################################################

    # Configure AWG parameters
    awg.configure(res=res, fs=fs, out1='dac', cf1=cf, func1=func1)

    # Define baseband iq waveform (i is ones and q is zeroes).
    bbfs = awg.fs / awg.intFactor
    rl = int(bbfs / cf * awg.gran)
    i = np.ones(rl)
    q = np.zeros(rl)

    # Interleave i and q into a single waveform and download to segment 1.
    awg.download_iq_wfm(i, q, ch=1)

    # Assign segment 1 to trace (channel) 1 and start continuous playback.
    awg.write('trace1:select 1')
    awg.write('output1:norm on')
    awg.write('init:cont on')
    awg.write('init:imm')
    awg.query('*opc?')

    # Check for errors and gracefully disconnect.
    awg.err_check()
    awg.disconnect()


if __name__ == '__main__':
    main()
