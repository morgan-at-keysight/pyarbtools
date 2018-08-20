"""
Digital Upconverter Chirped Pulse Generator for M8190 using pySource
Author: Morgan Allison
Updated: 07/18
Creates a chirped pulse using digital upconversion in the M8190.
Uses pySource.py for instrument communication.
Python 3.6.4
NumPy 1.14.2
Tested on M8190A
"""

import numpy as np
from pySource import *


def main():
    """Creates a chirped pulse using digital upconversion in the M8190."""
    awg = M8190A('141.121.210.171', reset=True)

    """User-defined sample rate, carrier frequency, chirp rate, pri, pulse width,
    resolution, ."""
    ############################################################################
    fs = 7.2e9
    cf = 1e9
    chirpRate = 100e9  # Hz/sec, can be positive or negative
    pri = 200e-6
    pw = 100e-6
    res = 'intx3'
    func1 = 'arb'
    ############################################################################

    # Configure AWG parameters
    awg.configure(res=res, fs=fs, out1='ac', cf1=cf, func1=func1)

    """Define baseband iq waveform. Create a time vector that goes from
    -1/2 to 1/2 instead of 0 to 1. This ensures that the chirp will be
    symmetrical around the carrier."""
    bbfs = awg.fs / awg.intFactor
    rl = bbfs * pw
    t = np.linspace(-rl / bbfs / 2, rl / bbfs / 2, rl, endpoint=False)

    """Direct phase manipulation was used to create the chirp modulation.
    https://en.wikipedia.org/wiki/Chirp#Linear
    phase = 2*pi*(f0*t + k/2*t^2)
    Since this is a baseband modulation scheme, there is no f0 term and the
    factors of 2 cancel out. It looks odd to have a pi multiplier rather than
    2*pi, but the math works out correctly. Just throw that into the complex
    exponential function and you're off to the races."""
    mod = np.pi * chirpRate * t**2
    iq = np.append(np.exp(1j * mod), np.zeros(int(bbfs * (pri - pw))))
    i = np.real(iq)
    q = np.imag(iq)

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
