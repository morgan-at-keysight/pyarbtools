"""
wfmBuilder
Author: Morgan Allison, Keysight RF/uW Application Engineer
Generic waveform creation capabilities for pyarbtools.
"""

import numpy as np
from scipy.signal import max_len_seq
from pyarbtools import communications
from pyarbtools import error


def sine_generator(fs=100e6, freq=0, phase=0, zeroLast=False, format='iq'):
    """Generates a sine wave with optional frequency offset and
    initial phase at baseband or RF."""

    if abs(freq) > fs / 2:
        raise error.WfmBuilderError('Frequency violates Nyquist.')

    if freq:
        time = 1000 / freq
    else:
        time = 10000 / fs
    print(time * fs)
    t = np.linspace(-time / 2, time / 2, int(time * fs), endpoint=False)
    if format.lower() == 'iq':
        iq = np.exp(2 * np.pi * freq * 1j * t) + phase
        if zeroLast:
            iq[-1] = 0 + 1j*0
        return iq.real, iq.imag
    elif format.lower() == 'real':
        real = np.cos(2 * np.pi * freq * t + phase)
        if zeroLast:
            real[-1] = 0
        return real
    else:
        raise error.WfmBuilderError('Invalid waveform format selected. Choose "iq" or "real".')


def am_generator(fs=100e6, amDepth=50, modRate=100e3, cf=1e9, format='iq'):
    """Generates a sinusoidal AM signal at baseband or RF."""

    if amDepth <= 0 or amDepth > 100:
        raise error.WfmBuilderError('AM Depth out of range, must be 0 - 100.')
    if modRate > fs:
        raise error.WfmBuilderError('Modulation rate violates Nyquist.')

    time = 1 / modRate
    t = np.linspace(-time / 2, time / 2, int(time * fs), endpoint=False)

    mod = (amDepth / 100) * np.sin(2 * np.pi * modRate * t) + 1

    if format.lower() == 'iq':
        iq = mod * np.exp(1j * t)
        sFactor = abs(np.amax(iq))
        iq = iq / sFactor * 0.707

        i = np.real(iq)
        q = np.imag(iq)
        return i, q
    elif format.lower() == 'real':
        real = mod * np.cos(2 * np.pi * cf * t)
        sFactor = np.amax(real)
        real = real / sFactor
        return real
    else:
        raise error.WfmBuilderError('Invalid waveform format selected. Choose "iq" or "real".')


def chirp_generator(fs=100e6, pWidth=10e-6, pri=100e-6, chirpBw=20e6, zeroLast=False, cf=1e9, format='iq'):
    """Generates a symmetrical linear chirp at baseband or RF. Chirp direction
    is determined by the sign of chirpBw (pos=up chirp, neg=down chirp)."""

    if chirpBw > fs:
        raise error.WfmBuilderError('Chirp Bandwidth violates Nyquist.')
    if chirpBw <= 0:
        raise error.WfmBuilderError('Chirp Bandwidth must be a positive value.')
    if pWidth <= 0 or pri <= 0:
        raise error.WfmBuilderError('Pulse width and PRI must be positive values.')

    """Define baseband iq waveform. Create a time vector that goes from
    -1/2 to 1/2 instead of 0 to 1. This ensures that the chirp will be
    symmetrical around the carrier."""

    rl = int(fs * pWidth)
    chirpRate = chirpBw / pWidth
    t = np.linspace(-rl / fs / 2, rl / fs / 2, rl, endpoint=False)

    """Direct phase manipulation was used to create the chirp modulation.
    https://en.wikipedia.org/wiki/Chirp#Linear
    phase = 2*pi*(f0*t + k/2*t^2)
    Since this is a baseband modulation scheme, there is no f0 term and the
    factors of 2 cancel out. It looks odd to have a pi multiplier rather than
    2*pi, but the math works out correctly. Just throw that into the complex
    exponential function and you're off to the races."""

    mod = np.pi * chirpRate * t**2
    if format.lower() == 'iq':
        iq = np.exp(1j * mod)
        if zeroLast:
            iq[-1] = 0 + 1j*0
        if pri <= pWidth:
            i = np.real(iq)
            q = np.imag(iq)
        else:
            deadTime = np.zeros(int(fs * pri - rl))
            i = np.append(np.real(iq), deadTime)
            q = np.append(np.imag(iq), deadTime)

        return i, q
    elif format.lower() == 'real':
        if pri <= pWidth:
            real = np.cos(2 * np.pi * cf * t + mod)
        else:
            deadTime = np.zeros(int(fs * pri - rl))
            real = np.append(np.cos(2 * np.pi * cf * t + mod), deadTime)

        return real
    else:
        raise error.WfmBuilderError('Invalid waveform format selected. Choose "iq" or "real".')


def barker_generator(fs=100e6, pWidth=10e-6, pri=100e-6, code='b2', zeroLast=False, cf=1e9, format='iq'):
    """Generates a Barker phase coded signal at baseband or RF."""
    if pWidth <= 0 or pri <= 0:
        raise error.WfmBuilderError('Pulse width and PRI must be positive values.')

    # Codes taken from https://en.wikipedia.org/wiki/Barker_code
    barkerCodes = {'b2': [1, -1], 'b3': [1, 1, -1],
                   'b41': [1, 1, -1, 1], 'b42': [1, 1, 1, -1],
                   'b5': [1, 1, 1, -1, 1], 'b7': [1, 1, 1, -1, -1, 1, -1],
                   'b11': [1, 1, 1, -1, -1, -1, 1, -1, -1, 1, -1],
                   'b13': [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1]}

    # Create array for each phase shift and concatenate them
    codeSamples = int(pWidth / len(barkerCodes[code]) * fs)
    rl = codeSamples * len(barkerCodes[code])
    barker = []
    for p in barkerCodes[code]:
        temp = np.full((codeSamples,), p)
        barker = np.concatenate([barker, temp])

    mod = np.pi / 2 * barker
    if format.lower() == 'iq':
        iq = np.exp(1j * mod)

        if zeroLast:
            iq[-1] = 0 + 0j
        if pri <= pWidth:
            i = np.real(iq)
            q = np.imag(iq)
        else:
            deadTime = np.zeros(int(fs * pri - rl))
            i = np.append(np.real(iq), deadTime)
            q = np.append(np.imag(iq), deadTime)

        return i, q
    elif format.lower() == 'real':
        t = np.linspace(-rl / fs / 2, rl / fs / 2, rl, endpoint=False)

        if pri <= pWidth:
            real = np.cos(2 * np.pi * cf * t + mod)
        else:
            deadTime = np.zeros(int(fs * pri - rl))
            real = np.append(np.cos(2 * np.pi * cf * t + mod), deadTime)

        return real
    else:
        raise error.WfmBuilderError('Invalid waveform format selected. Choose "iq" or "real".')


def rrc_filter(taps, a, symRate, fs):
    """Generates the impulse response of a root raised cosine filter
    from user-defined number of taps, rolloff factor, symbol rate,
    and sample rate.
    RRC equation taken from https://en.wikipedia.org/wiki/Root-raised-cosine_filter"""

    dt = 1 / fs
    tau = 1 / symRate
    time = np.linspace(-taps / 2, taps / 2, taps, endpoint=False) * dt
    h = np.zeros(taps, dtype=float)

    for t, x in zip(time, range(len(h))):
        if t == 0.0:
            h[x] = 1.0 + a * (4 / np.pi - 1)
        elif a != 0 and (t == tau/(4*a) or t == -tau/(4*a)):
            h[x] = a / np.sqrt(2) * (((1 + 2 / np.pi) * (np.sin(np.pi / (4 * a))))
            + ((1 - 2 / np.pi) * (np.cos(np.pi / (4 * a)))))
        else:
            h[x] = (np.sin(np.pi * t / tau * (1 - a)) + 4 * a * t / tau * np.cos(np.pi * t / tau * (1 + a)))\
            / (np.pi * t / tau * (1 - (4 * a * t / tau) ** 2))

    return time, h


def rc_filter(taps, a, symRate, fs):
    """Generates the impulse response of a raised cosine filter
    from user-defined number of taps, rolloff factor, symbol rate,
    and sample rate.
    RC equation taken from https://en.wikipedia.org/wiki/Raised-cosine_filter"""

    dt = 1 / fs
    tau = 1 / symRate
    time = np.linspace(-taps / 2, taps / 2, taps, endpoint=False) * dt
    h = np.zeros(taps, dtype=float)

    for t, x in zip(time, range(len(h))):
        if t == 0.0:
            h[x] = 1.0
        elif a != 0 and (t == tau / (2 * a) or t == -tau / (2 * a)):
            h[x] = np.pi / (4 * tau) * np.sinc(1 / (2 * a))
        else:
            h[x] = 1 / tau * np.sinc(t / tau) * np.cos(np.pi * a * t / tau) / (1 - (2 * a * t / tau) ** 2)

    return time, h


def bpsk_modulator(data, customMap=None):
    """Converts list of bits to symbol values as strings, maps each
    symbol value to a position on the complex plane, and returns an
    array of complex values for BPSK.

    customMap is a dict whos keys are strings containing the symbol's
    binary value and whos values are the symbol's location in the
    complex plane.
    e.g. customMap = {'0101': 0.707 + 0.707j, ...} """

    pattern = [str(d) for d in data]
    if customMap:
        bpskMap = customMap
    else:
        bpskMap = {'0': 1 + 0j, '1': -1 + 0j}

    try:
        return np.array([bpskMap[p] for p in pattern])
    except KeyError:
        raise ValueError('Invalid BPSK symbol value.')


def qpsk_modulator(data, customMap=None):
    """Converts list of bits to symbol values as strings, maps each
    symbol value to a position on the complex plane, and returns an
    array of complex values for QPSK.

    customMap is a dict whos keys are strings containing the symbol's
    binary value and whos values are the symbol's location in the
    complex plane.
    e.g. customMap = {'0101': 0.707 + 0.707j, ...}
    """

    pattern = [str(d0) + str(d1) for d0, d1 in zip(data[0::2], data[1::2])]
    if customMap:
        qpskMap = customMap
    else:
        qpskMap = {'00': 1 + 1j, '01': -1 + 1j, '10': -1 - 1j, '11': 1 - 1j}

    try:
        return np.array([qpskMap[p] for p in pattern])
    except KeyError:
        raise ValueError('Invalid QPSK symbol.')


def psk8_modulator(data, customMap=None):
    """Converts list of bits to symbol values as strings, maps each
    symbol value to a position on the complex plane, and returns an
    array of complex values for 8-PSK.

    customMap is a dict whos keys are strings containing the symbol's
    binary value and whos values are the symbol's location in the
    complex plane.
    e.g. customMap = {'0101': 0.707 + 0.707j, ...}
    """

    pattern = [str(d0) + str(d1) + str(d2) for d0, d1, d2 in
               zip(data[0::3], data[1::3], data[2::3])]
    if customMap:
        psk8Map = customMap
    else:
        psk8Map = {'000': 1 + 0j, '001': 0.707 + 0.707j, '010': 0 + 1j,
                   '011': -0.707 + 0.707j, '100': -1 + 0j,
                   '101': -0.707 - 0.707j, '110': 0 - 1j,
                   '111': 0.707 - 0.707j}

    try:
        return np.array([psk8Map[p] for p in pattern])
    except KeyError:
        raise ValueError('Invalid 8PSK symbol.')


def psk16_modulator(data, customMap=None):
    """Converts list of bits to symbol values as strings, maps each
    symbol value to a position on the complex plane, and returns an
    array of complex values for 16-PSK.

    customMap is a dict whos keys are strings containing the symbol's
    binary value and whos values are the symbol's location in the
    complex plane.
    e.g. customMap = {'0101': 0.707 + 0.707j, ...}
    """

    pattern = [str(d0) + str(d1) + str(d2) + str(d3) for d0, d1, d2, d3 in
               zip(data[0::4], data[1::4], data[2::4], data[3::4])]
    if customMap:
        psk16Map = customMap
    else:
        psk16Map = {'0000': 1 + 0j, '0001': 0.923880 + 0.382683j,
                   '0010': 0.707107 + 0.707107j, '0011': 0.382683 + 0.923880j,
                   '0100': 0 + 1j, '0101': -0.382683 + 0.923880j,
                   '0110': -0.707107 + 0.707107j, '0111': -0.923880 + 0.382683j,
                   '1000': -1 + 0j, '1001': -0.923880 - 0.382683j,
                   '1010': -0.707107 - 0.707107j, '1011': -0.382683 - 0.923880j,
                   '1100': 0 - 1j, '1101': 0.382683 - 0.923880j,
                   '1110': 0.707107 - 0.707107j, '1111': 0.923880 - 0.382683j}

    try:
        return np.array([psk16Map[p] for p in pattern])
    except KeyError:
        raise ValueError('Invalid 8PSK symbol.')


def qam16_modulator(data, customMap=None):
    """Converts list of bits to symbol values as strings, maps each
    symbol value to a position on the complex plane, and returns an
    array of complex values for 16 QAM.

    A 4-variable Karnaugh map is used to determine the default symbol
    locations to prevent adjacent symbol errors from differing more
    than 1 bit from the intended symbol.
    https://www.gaussianwaves.com/2012/10/constructing-a-rectangular-constellation-for-16-qam/

    customMap is a dict whos keys are strings containing the symbol's
    binary value and whos values are the symbol's location in the
    complex plane.
    e.g. customMap = {'0101': 0.707 + 0.707j, ...} """

    pattern = [str(d0) + str(d1) + str(d2) + str(d3) for d0, d1, d2, d3 in
               zip(data[0::4], data[1::4], data[2::4], data[3::4])]
    if customMap:
        qamMap = customMap
    else:
        qamMap = {'0000': -3 - 3j, '0001': -3 - 1j, '0010': -3 + 3j,
                  '0011': -3 + 1j, '0100': -1 - 3j, '0101': -1 - 1j,
                  '0110': -1 + 3j, '0111': -1 + 1j, '1000': 3 - 3j,
                  '1001': 3 - 1j, '1010': 3 + 3j, '1011': 3 + 1j,
                  '1100': 1 - 3j, '1101': 1 - 1j, '1110': 1 + 3j,
                  '1111': 1 + 1j}
    try:
        return np.array([qamMap[p] for p in pattern])
    except KeyError:
        raise ValueError('Invalid 16 QAM symbol.')


def qam32_modulator(data, customMap=None):
    """Converts list of bits to symbol values as strings, maps each
    symbol value to a position on the complex plane, and returns an
    array of complex values for 32 QAM.

    A 5-variable Karnaugh map is used to determine the default symbol
    locations to prevent adjacent symbol errors from differing more
    than 1 bit from the intended symbol.

    customMap is a dict whos keys are strings containing the symbol's
    binary value and whos values are the symbol's location in the
    complex plane.
    e.g. customMap = {'0101': 0.707 + 0.707j, ...} """

    pattern = [str(d0) + str(d1) + str(d2) + str(d3) + str(d4) for d0, d1, d2, d3, d4 in
               zip(data[0::5], data[1::5], data[2::5], data[3::5], data[4::5])]
    if customMap:
        qamMap = customMap
    else:
        qamMap = {'00000': -3 + 5j, '00001': -5 - 1j, '00010': 3 + 3j,
                  '00011': -3 - 1j, '00100': -5 + 3j, '00101': 3 - 1j,
                  '00110': -1 + 1j, '00111': -3 - 5j, '01000': 1 + 5j,
                  '01001': -1 - 1j, '01010': -5 + 1j, '01011': 3 - 3j,
                  '01100': -1 + 3j, '01101': -5 - 3j, '01110': 3 + 1j,
                  '01111': 1 - 5j, '10000': -1 + 5j, '10001': -3 - 1j,
                  '10010': 5 + 3j, '10011': 1 - 3j, '10100': -3 + 3j,
                  '10101': 5 - 1j, '10110': 1 + 1j, '10111': -1 - 5j,
                  '11000': 3 + 5j, '11001': 1 - 1j, '11010': -3 + 1j,
                  '11011': 5 - 3j, '11100': 1 + 3j, '11101': -3 - 3j,
                  '11110': 5 + 1j, '11111': 3 - 3j}
    try:
        return np.array([qamMap[p] for p in pattern])
    except KeyError:
        raise ValueError('Invalid 32 QAM symbol.')


def qam64_modulator(data, customMap=None):
    """Converts list of bits to symbol values as strings, maps each
    symbol value to a position on the complex plane, and returns an
    array of complex values for 64 QAM.

    A 6-variable Karnaugh map is used to determine the default symbol
    locations to prevent adjacent symbol errors from differing more
    than 1 bit from the intended symbol.

    customMap is a dict whos keys are strings containing the symbol's
    binary value and whos values are the symbol's location in the
    complex plane.
    e.g. customMap = {'0101': 0.707 + 0.707j, ...} """

    pattern = [str(d0) + str(d1) + str(d2) + str(d3) + str(d4) + str(d5) for d0, d1, d2, d3, d4, d5 in
               zip(data[0::6], data[1::6], data[2::6], data[3::6], data[4::6], data[5::6])]
    if customMap:
        qamMap = customMap
    else:
        qamMap = {'000000': 7 + 7j, '000001': 7 + 5j, '000010': 5 + 7j,
                  '000011': 5 + 5j, '000100': 7 + 1j, '000101': 7 + 3j,
                  '000110': 5 + 1j, '000111': 5 + 3j, '001000': 1 + 7j,
                  '001001': 1 + 5j, '001010': 3 + 7j, '001011': 3 + 5j,
                  '001100': 1 + 1j, '001101': 1 + 3j, '001110': 3 + 1j,
                  '001111': 3 + 3j, '010000': 7 - 7j, '010001': 7 - 5j,
                  '010010': 5 - 7j, '010011': 5 - 5j, '010100': 7 - 1j,
                  '010101': 7 - 3j, '010110': 5 - 1j, '010111': 5 - 3j,
                  '011000': 1 - 7j, '011001': 1 - 5j, '011010': 3 - 7j,
                  '011011': 3 - 5j, '011100': 1 - 1j, '011101': 1 - 3j,
                  '011110': 3 - 1j, '011111': 3 - 3j,
                  '100000': -7 + 7j, '100001': -7 + 5j, '100010': -5 + 7j,
                  '100011': -5 + 5j, '100100': -7 + 1j, '100101': -7 + 3j,
                  '100110': -5 + 1j, '100111': -5 + 3j, '101000': -1 + 7j,
                  '101001': -1 + 5j, '101010': -3 + 7j, '101011': -3 + 5j,
                  '101100': -1 + 1j, '101101': -1 + 3j, '101110': -3 + 1j,
                  '101111': -3 + 3j, '110000': -7 - 7j, '110001': -7 - 5j,
                  '110010': -5 - 7j, '110011': -5 - 5j, '110100': -7 - 1j,
                  '110101': -7 - 3j, '110110': -5 - 1j, '110111': -5 - 3j,
                  '111000': -1 - 7j, '111001': -1 - 5j, '111010': -3 - 7j,
                  '111011': -3 - 5j, '111100': -1 - 1j, '111101': -1 - 3j,
                  '111110': -3 - 1j, '111111': -3 - 3j}
    try:
        return np.array([qamMap[p] for p in pattern])
    except KeyError:
        raise ValueError('Invalid 64 QAM symbol.')


def qam128_modulator(data, customMap=None):
    """Converts list of bits to symbol values as strings, maps each
    symbol value to a position on the complex plane, and returns an
    array of complex values for 128 QAM.

    A 7-variable Karnaugh map is used to determine the default symbol
    locations to prevent adjacent symbol errors from differing more
    than 1 bit from the intended symbol.

    customMap is a dict whos keys are strings containing the symbol's
    binary value and whos values are the symbol's location in the
    complex plane.
    e.g. customMap = {'0101': 0.707 + 0.707j, ...} """

    pattern = [str(d0) + str(d1) + str(d2) + str(d3) + str(d4) + str(d5) + str(d6) for d0, d1, d2, d3, d4, d5, d6 in
               zip(data[0::7], data[1::7], data[2::7], data[3::7], data[4::7], data[5::7], data[6::7])]
    if customMap:
        qamMap = customMap
    else:
        qamMap = {'0000000': 1 + 1j, '0000001': 1 + 3j, '0000010': 1 + 5j, '0000011': 1 + 7j,
                  '0000100': 1 + 9j, '0000101': 1 + 11j, '0000110': 1 - 11j, '0000111': 1 - 9j,
                  '0001000': 1 - 7j, '0001001': 1 - 5j, '0001010': 1 - 3j, '0001011': 1 - 1j,
                  '0001100': 3 + 1j, '0001101': 3 + 3j, '0001110': 3 + 5j, '0001111': 3 + 7j,
                  '0010000': 3 + 9j, '0010001': 3 + 11j, '0010010': 3 - 11j, '0010011': 3 - 9j,
                  '0010100': 3 - 7j, '0010101': 3 - 5j, '0010110': 3 - 3j, '0010111': 3 - 1j,
                  '0011000': 5 + 1j, '0011001': 5 + 3j, '0011010': 5 + 5j, '0011011': 5 + 7j,
                  '0011100': 5 + 9j, '0011101': 5 + 11j, '0011110': 5 - 11j, '0011111': 5 - 9j,
                  '0100000': 5 - 7j, '0100001': 5 - 5j, '0100010': 5 - 3j, '0100011': 5 - 1j,
                  '0100100': 7 + 1j, '0100101': 7 + 3j, '0100110': 7 + 5j, '0100111': 7 + 7j,
                  '0101000': 7 + 9j, '0101001': 7 + 11j, '0101010': 7 - 11j, '0101011': 7 - 9j,
                  '0101100': 7 - 7j, '0101101': 7 - 5j, '0101110': 7 - 3j, '0101111': 7 - 1j,
                  '0110000': 9 + 1j, '0110001': 9 + 3j, '0110010': 9 + 5j, '0110011': 9 + 7j,
                  '0110100': 9 - 7j, '0110101': 9 - 5j, '0110110': 9 - 3j, '0110111': 9 - 1j,
                  '0111000': 1 + 1j, '0111001': 1 + 3j, '0111010': 1 + 5j, '0111011': 1 + 7j,
                  '0111100': 1 - 7j, '0111101': 1 - 5j, '0111110': 1 - 3j, '0111111': 1 - 1j,
                  '1000000': -1 + 1j, '1000001': -1 + 3j, '1000010': -1 + 5j, '1000011': -1 + 7j,
                  '1000100': -1 - 7j, '1000101': -1 - 5j, '1000110': -1 - 3j, '1000111': -1 - 1j,
                  '1001000': -9 + 1j, '1001001': -9 + 3j, '1001010': -9 + 5j, '1001011': -9 + 7j,
                  '1001100': -9 - 7j, '1001101': -9 - 5j, '1001110': -9 - 3j, '1001111': -9 - 1j,
                  '1010000': -7 + 1j, '1010001': -7 + 3j, '1010010': -7 + 5j, '1010011': -7 + 7j,
                  '1010100': -7 + 9j, '1010101': -7 + 11j, '1010110': -7 - 11j, '1010111': -7 - 9j,
                  '1011000': -7 - 7j, '1011001': -7 - 5j, '1011010': -7 - 3j, '1011011': -7 - 1j,
                  '1011100': -5 + 1j, '1011101': -5 + 3j, '1011110': -5 + 5j, '1011111': -5 + 7j,
                  '1100000': -5 + 9j, '1100001': -5 + 11j, '1100010': -5 - 11j, '1100011': -5 - 9j,
                  '1100100': -5 - 7j, '1100101': -5 - 5j, '1100110': -5 - 3j, '1100111': -5 - 1j,
                  '1101000': -3 + 1j, '1101001': -3 + 3j, '1101010': -3 + 5j, '1101011': -3 + 7j,
                  '1101100': -3 + 9j, '1101101': -3 + 11j, '1101110': -3 - 11j, '1101111': -3 - 9j,
                  '1110000': -3 - 7j, '1110001': -3 - 5j, '1110010': -3 - 3j, '1110011': -3 - 1j,
                  '1110100': -1 + 1j, '1110101': -1 + 3j, '1110110': -1 + 5j, '1110111': -1 + 7j,
                  '1111000': -1 + 9j, '1111001': -1 + 11j, '1111010': -1 - 11j, '1111011': -1 - 9j,
                  '1111100': -1 - 7j, '1111101': -1 - 5j, '1111110': -1 - 3j, '1111111': -1 - 1j}
    try:
        return np.array([qamMap[p] for p in pattern])
    except KeyError:
        raise ValueError('Invalid 128 QAM symbol.')


def qam256_modulator(data, customMap=None):
    """Converts list of bits to symbol values as strings, maps each
    symbol value to a position on the complex plane, and returns an
    array of complex values for 256 QAM.

    An 8-variable Karnaugh map is used to determine the default symbol
    locations to prevent adjacent symbol errors from differing more
    than 1 bit from the intended symbol.

    customMap is a dict whos keys are strings containing the symbol's
    binary value and whos values are the symbol's location in the
    complex plane.
    e.g. customMap = {'0101': 0.707 + 0.707j, ...} """

    pattern = [str(d0) + str(d1) + str(d2) + str(d3) + str(d4) + str(d5) + str(d6) + str(d7) for d0, d1, d2, d3, d4, d5, d6, d7 in
               zip(data[0::8], data[1::8], data[2::8], data[3::8], data[4::8], data[5::8], data[6::8], data[7::8])]
    if customMap:
        qamMap = customMap
    else:
        qamMap = {'00000000': +0.06666666667 + 0.06666666667j,
                  '00000001': +0.06666666667 + 0.20000000000j,
                  '00000010': +0.06666666667 + 0.33333333333j,
                  '00000011': +0.06666666667 + 0.46666666667j,
                  '00000100': +0.06666666667 + 0.60000000000j,
                  '00000101': +0.06666666667 + 0.73333333333j,
                  '00000110': +0.06666666667 + 0.86666666667j,
                  '00000111': +0.06666666667 + 1.00000000000j,
                  '00001000': +0.06666666667 - 1.00000000000j,
                  '00001001': +0.06666666667 - 0.86666666667j,
                  '00001010': +0.06666666667 - 0.73333333333j,
                  '00001011': +0.06666666667 - 0.60000000000j,
                  '00001100': +0.06666666667 - 0.46666666667j,
                  '00001101': +0.06666666667 - 0.33333333333j,
                  '00001110': +0.06666666667 - 0.20000000000j,
                  '00001111': +0.06666666667 - 0.06666666667j,
                  '00010000': +0.20000000000 + 0.06666666667j,
                  '00010001': +0.20000000000 + 0.20000000000j,
                  '00010010': +0.20000000000 + 0.33333333333j,
                  '00010011': +0.20000000000 + 0.46666666667j,
                  '00010100': +0.20000000000 + 0.60000000000j,
                  '00010101': +0.20000000000 + 0.73333333333j,
                  '00010110': +0.20000000000 + 0.86666666667j,
                  '00010111': +0.20000000000 + 1.00000000000j,
                  '00011000': +0.20000000000 - 1.00000000000j,
                  '00011001': +0.20000000000 - 0.86666666667j,
                  '00011010': +0.20000000000 - 0.73333333333j,
                  '00011011': +0.20000000000 - 0.60000000000j,
                  '00011100': +0.20000000000 - 0.46666666667j,
                  '00011101': +0.20000000000 - 0.33333333333j,
                  '00011110': +0.20000000000 - 0.20000000000j,
                  '00011111': +0.20000000000 - 0.06666666667j,
                  '00100000': +0.33333333333 + 0.06666666667j,
                  '00100001': +0.33333333333 + 0.20000000000j,
                  '00100010': +0.33333333333 + 0.33333333333j,
                  '00100011': +0.33333333333 + 0.46666666667j,
                  '00100100': +0.33333333333 + 0.60000000000j,
                  '00100101': +0.33333333333 + 0.73333333333j,
                  '00100110': +0.33333333333 + 0.86666666667j,
                  '00100111': +0.33333333333 + 1.00000000000j,
                  '00101000': +0.33333333333 - 1.00000000000j,
                  '00101001': +0.33333333333 - 0.86666666667j,
                  '00101010': +0.33333333333 - 0.73333333333j,
                  '00101011': +0.33333333333 - 0.60000000000j,
                  '00101100': +0.33333333333 - 0.46666666667j,
                  '00101101': +0.33333333333 - 0.33333333333j,
                  '00101110': +0.33333333333 - 0.20000000000j,
                  '00101111': +0.33333333333 - 0.06666666667j,
                  '00110000': +0.46666666667 + 0.06666666667j,
                  '00110001': +0.46666666667 + 0.20000000000j,
                  '00110010': +0.46666666667 + 0.33333333333j,
                  '00110011': +0.46666666667 + 0.46666666667j,
                  '00110100': +0.46666666667 + 0.60000000000j,
                  '00110101': +0.46666666667 + 0.73333333333j,
                  '00110110': +0.46666666667 + 0.86666666667j,
                  '00110111': +0.46666666667 + 1.00000000000j,
                  '00111000': +0.46666666667 - 1.00000000000j,
                  '00111001': +0.46666666667 - 0.86666666667j,
                  '00111010': +0.46666666667 - 0.73333333333j,
                  '00111011': +0.46666666667 - 0.60000000000j,
                  '00111100': +0.46666666667 - 0.46666666667j,
                  '00111101': +0.46666666667 - 0.33333333333j,
                  '00111110': +0.46666666667 - 0.20000000000j,
                  '00111111': +0.46666666667 - 0.06666666667j,
                  '01000000': +0.60000000000 + 0.06666666667j,
                  '01000001': +0.60000000000 + 0.20000000000j,
                  '01000010': +0.60000000000 + 0.33333333333j,
                  '01000011': +0.60000000000 + 0.46666666667j,
                  '01000100': +0.60000000000 + 0.60000000000j,
                  '01000101': +0.60000000000 + 0.73333333333j,
                  '01000110': +0.60000000000 + 0.86666666667j,
                  '01000111': +0.60000000000 + 1.00000000000j,
                  '01001000': +0.60000000000 - 1.00000000000j,
                  '01001001': +0.60000000000 - 0.86666666667j,
                  '01001010': +0.60000000000 - 0.73333333333j,
                  '01001011': +0.60000000000 - 0.60000000000j,
                  '01001100': +0.60000000000 - 0.46666666667j,
                  '01001101': +0.60000000000 - 0.33333333333j,
                  '01001110': +0.60000000000 - 0.20000000000j,
                  '01001111': +0.60000000000 - 0.06666666667j,
                  '01010000': +0.73333333333 + 0.06666666667j,
                  '01010001': +0.73333333333 + 0.20000000000j,
                  '01010010': +0.73333333333 + 0.33333333333j,
                  '01010011': +0.73333333333 + 0.46666666667j,
                  '01010100': +0.73333333333 + 0.60000000000j,
                  '01010101': +0.73333333333 + 0.73333333333j,
                  '01010110': +0.73333333333 + 0.86666666667j,
                  '01010111': +0.73333333333 + 1.00000000000j,
                  '01011000': +0.73333333333 - 1.00000000000j,
                  '01011001': +0.73333333333 - 0.86666666667j,
                  '01011010': +0.73333333333 - 0.73333333333j,
                  '01011011': +0.73333333333 - 0.60000000000j,
                  '01011100': +0.73333333333 - 0.46666666667j,
                  '01011101': +0.73333333333 - 0.33333333333j,
                  '01011110': +0.73333333333 - 0.20000000000j,
                  '01011111': +0.73333333333 - 0.06666666667j,
                  '01100000': +0.86666666667 + 0.06666666667j,
                  '01100001': +0.86666666667 + 0.20000000000j,
                  '01100010': +0.86666666667 + 0.33333333333j,
                  '01100011': +0.86666666667 + 0.46666666667j,
                  '01100100': +0.86666666667 + 0.60000000000j,
                  '01100101': +0.86666666667 + 0.73333333333j,
                  '01100110': +0.86666666667 + 0.86666666667j,
                  '01100111': +0.86666666667 + 1.00000000000j,
                  '01101000': +0.86666666667 - 1.00000000000j,
                  '01101001': +0.86666666667 - 0.86666666667j,
                  '01101010': +0.86666666667 - 0.73333333333j,
                  '01101011': +0.86666666667 - 0.60000000000j,
                  '01101100': +0.86666666667 - 0.46666666667j,
                  '01101101': +0.86666666667 - 0.33333333333j,
                  '01101110': +0.86666666667 - 0.20000000000j,
                  '01101111': +0.86666666667 - 0.06666666667j,
                  '01110000': +1.00000000000 + 0.06666666667j,
                  '01110001': +1.00000000000 + 0.20000000000j,
                  '01110010': +1.00000000000 + 0.33333333333j,
                  '01110011': +1.00000000000 + 0.46666666667j,
                  '01110100': +1.00000000000 + 0.60000000000j,
                  '01110101': +1.00000000000 + 0.73333333333j,
                  '01110110': +1.00000000000 + 0.86666666667j,
                  '01110111': +1.00000000000 + 1.00000000000j,
                  '01111000': +1.00000000000 - 1.00000000000j,
                  '01111001': +1.00000000000 - 0.86666666667j,
                  '01111010': +1.00000000000 - 0.73333333333j,
                  '01111011': +1.00000000000 - 0.60000000000j,
                  '01111100': +1.00000000000 - 0.46666666667j,
                  '01111101': +1.00000000000 - 0.33333333333j,
                  '01111110': +1.00000000000 - 0.20000000000j,
                  '01111111': +1.00000000000 - 0.06666666667j,
                  '10000000': -1.00000000000 + 0.06666666667j,
                  '10000001': -1.00000000000 + 0.20000000000j,
                  '10000010': -1.00000000000 + 0.33333333333j,
                  '10000011': -1.00000000000 + 0.46666666667j,
                  '10000100': -1.00000000000 + 0.60000000000j,
                  '10000101': -1.00000000000 + 0.73333333333j,
                  '10000110': -1.00000000000 + 0.86666666667j,
                  '10000111': -1.00000000000 + 1.00000000000j,
                  '10001000': -1.00000000000 - 1.00000000000j,
                  '10001001': -1.00000000000 - 0.86666666667j,
                  '10001010': -1.00000000000 - 0.73333333333j,
                  '10001011': -1.00000000000 - 0.60000000000j,
                  '10001100': -1.00000000000 - 0.46666666667j,
                  '10001101': -1.00000000000 - 0.33333333333j,
                  '10001110': -1.00000000000 - 0.20000000000j,
                  '10001111': -1.00000000000 - 0.06666666667j,
                  '10010000': -0.86666666667 + 0.06666666667j,
                  '10010001': -0.86666666667 + 0.20000000000j,
                  '10010010': -0.86666666667 + 0.33333333333j,
                  '10010011': -0.86666666667 + 0.46666666667j,
                  '10010100': -0.86666666667 + 0.60000000000j,
                  '10010101': -0.86666666667 + 0.73333333333j,
                  '10010110': -0.86666666667 + 0.86666666667j,
                  '10010111': -0.86666666667 + 1.00000000000j,
                  '10011000': -0.86666666667 - 1.00000000000j,
                  '10011001': -0.86666666667 - 0.86666666667j,
                  '10011010': -0.86666666667 - 0.73333333333j,
                  '10011011': -0.86666666667 - 0.60000000000j,
                  '10011100': -0.86666666667 - 0.46666666667j,
                  '10011101': -0.86666666667 - 0.33333333333j,
                  '10011110': -0.86666666667 - 0.20000000000j,
                  '10011111': -0.86666666667 - 0.06666666667j,
                  '10100000': -0.73333333333 + 0.06666666667j,
                  '10100001': -0.73333333333 + 0.20000000000j,
                  '10100010': -0.73333333333 + 0.33333333333j,
                  '10100011': -0.73333333333 + 0.46666666667j,
                  '10100100': -0.73333333333 + 0.60000000000j,
                  '10100101': -0.73333333333 + 0.73333333333j,
                  '10100110': -0.73333333333 + 0.86666666667j,
                  '10100111': -0.73333333333 + 1.00000000000j,
                  '10101000': -0.73333333333 - 1.00000000000j,
                  '10101001': -0.73333333333 - 0.86666666667j,
                  '10101010': -0.73333333333 - 0.73333333333j,
                  '10101011': -0.73333333333 - 0.60000000000j,
                  '10101100': -0.73333333333 - 0.46666666667j,
                  '10101101': -0.73333333333 - 0.33333333333j,
                  '10101110': -0.73333333333 - 0.20000000000j,
                  '10101111': -0.73333333333 - 0.06666666667j,
                  '10110000': -0.60000000000 + 0.06666666667j,
                  '10110001': -0.60000000000 + 0.20000000000j,
                  '10110010': -0.60000000000 + 0.33333333333j,
                  '10110011': -0.60000000000 + 0.46666666667j,
                  '10110100': -0.60000000000 + 0.60000000000j,
                  '10110101': -0.60000000000 + 0.73333333333j,
                  '10110110': -0.60000000000 + 0.86666666667j,
                  '10110111': -0.60000000000 + 1.00000000000j,
                  '10111000': -0.60000000000 - 1.00000000000j,
                  '10111001': -0.60000000000 - 0.86666666667j,
                  '10111010': -0.60000000000 - 0.73333333333j,
                  '10111011': -0.60000000000 - 0.60000000000j,
                  '10111100': -0.60000000000 - 0.46666666667j,
                  '10111101': -0.60000000000 - 0.33333333333j,
                  '10111110': -0.60000000000 - 0.20000000000j,
                  '10111111': -0.60000000000 - 0.06666666667j,
                  '11000000': -0.46666666667 + 0.06666666667j,
                  '11000001': -0.46666666667 + 0.20000000000j,
                  '11000010': -0.46666666667 + 0.33333333333j,
                  '11000011': -0.46666666667 + 0.46666666667j,
                  '11000100': -0.46666666667 + 0.60000000000j,
                  '11000101': -0.46666666667 + 0.73333333333j,
                  '11000110': -0.46666666667 + 0.86666666667j,
                  '11000111': -0.46666666667 + 1.00000000000j,
                  '11001000': -0.46666666667 - 1.00000000000j,
                  '11001001': -0.46666666667 - 0.86666666667j,
                  '11001010': -0.46666666667 - 0.73333333333j,
                  '11001011': -0.46666666667 - 0.60000000000j,
                  '11001100': -0.46666666667 - 0.46666666667j,
                  '11001101': -0.46666666667 - 0.33333333333j,
                  '11001110': -0.46666666667 - 0.20000000000j,
                  '11001111': -0.46666666667 - 0.06666666667j,
                  '11010000': -0.33333333333 + 0.06666666667j,
                  '11010001': -0.33333333333 + 0.20000000000j,
                  '11010010': -0.33333333333 + 0.33333333333j,
                  '11010011': -0.33333333333 + 0.46666666667j,
                  '11010100': -0.33333333333 + 0.60000000000j,
                  '11010101': -0.33333333333 + 0.73333333333j,
                  '11010110': -0.33333333333 + 0.86666666667j,
                  '11010111': -0.33333333333 + 1.00000000000j,
                  '11011000': -0.33333333333 - 1.00000000000j,
                  '11011001': -0.33333333333 - 0.86666666667j,
                  '11011010': -0.33333333333 - 0.73333333333j,
                  '11011011': -0.33333333333 - 0.60000000000j,
                  '11011100': -0.33333333333 - 0.46666666667j,
                  '11011101': -0.33333333333 - 0.33333333333j,
                  '11011110': -0.33333333333 - 0.20000000000j,
                  '11011111': -0.33333333333 - 0.06666666667j,
                  '11100000': -0.20000000000 + 0.06666666667j,
                  '11100001': -0.20000000000 + 0.20000000000j,
                  '11100010': -0.20000000000 + 0.33333333333j,
                  '11100011': -0.20000000000 + 0.46666666667j,
                  '11100100': -0.20000000000 + 0.60000000000j,
                  '11100101': -0.20000000000 + 0.73333333333j,
                  '11100110': -0.20000000000 + 0.86666666667j,
                  '11100111': -0.20000000000 + 1.00000000000j,
                  '11101000': -0.20000000000 - 1.00000000000j,
                  '11101001': -0.20000000000 - 0.86666666667j,
                  '11101010': -0.20000000000 - 0.73333333333j,
                  '11101011': -0.20000000000 - 0.60000000000j,
                  '11101100': -0.20000000000 - 0.46666666667j,
                  '11101101': -0.20000000000 - 0.33333333333j,
                  '11101110': -0.20000000000 - 0.20000000000j,
                  '11101111': -0.20000000000 - 0.06666666667j,
                  '11110000': -0.06666666667 + 0.06666666667j,
                  '11110001': -0.06666666667 + 0.20000000000j,
                  '11110010': -0.06666666667 + 0.33333333333j,
                  '11110011': -0.06666666667 + 0.46666666667j,
                  '11110100': -0.06666666667 + 0.60000000000j,
                  '11110101': -0.06666666667 + 0.73333333333j,
                  '11110110': -0.06666666667 + 0.86666666667j,
                  '11110111': -0.06666666667 + 1.00000000000j,
                  '11111000': -0.06666666667 - 1.00000000000j,
                  '11111001': -0.06666666667 - 0.86666666667j,
                  '11111010': -0.06666666667 - 0.73333333333j,
                  '11111011': -0.06666666667 - 0.60000000000j,
                  '11111100': -0.06666666667 - 0.46666666667j,
                  '11111101': -0.06666666667 - 0.33333333333j,
                  '11111110': -0.06666666667 - 0.20000000000j,
                  '11111111': -0.06666666667 - 0.06666666667j}

    try:
        return np.array([qamMap[p] for p in pattern])
    except KeyError:
        raise ValueError('Invalid 256 QAM symbol.')


def digmod_prbs_generator(fs=100e6, modType='qpsk', symRate=10e6, prbsOrder=9, filt=rrc_filter, alpha=0.35, zeroLast=False):
    """Generates a digitally modulated signal with a given modulation
    and filter type using PRBS data at baseband."""

    if symRate > fs:
        raise error.WfmBuilderError('Symbol Rate violates Nyquist.')

    saPerSym = int(fs / symRate)
    filterSymbolLength = 10

    # Define bits per symbol and modulator function based on modType
    if modType.lower() == 'bpsk':
        bitsPerSym = 1
        modulator = bpsk_modulator
    elif modType.lower() == 'qpsk':
        bitsPerSym = 2
        modulator = qpsk_modulator
    elif modType.lower() == '8psk':
        bitsPerSym = 3
        modulator = psk8_modulator
    elif modType.lower() == '16psk':
        bitsPerSym = 4
        modulator = psk16_modulator
    elif modType.lower() == 'qam16':
        bitsPerSym = 4
        modulator = qam16_modulator
    elif modType.lower() == 'qam32':
        bitsPerSym = 5
        modulator = qam32_modulator
    elif modType.lower() == 'qam64':
        bitsPerSym = 6
        modulator = qam64_modulator
    elif modType.lower() == 'qam128':
        bitsPerSym = 7
        modulator = qam128_modulator
    elif modType.lower() == 'qam256':
        bitsPerSym = 8
        modulator = qam256_modulator
    else:
        raise ValueError('Invalid modType chosen.')

    # Create pattern and repeat to ensure integer number of symbols.
    temp, state = max_len_seq(prbsOrder)
    bits = temp
    repeats = 1
    while len(bits) % bitsPerSym:
        bits = np.tile(temp, repeats)
        repeats += 1

    """Convert the pseudorandom bit sequence, which is a list of bits,
    into the binary values of symbols as strings, and then map symbols
    to locations in the complex plane."""
    symbols = modulator(bits)

    """Perform a pseudo circular convolution on the symbols to mitigate
    zeroing of samples due to filter delay (i.e. PREpend the
    last few symbols and APpend the first few symbols)."""
    symbols = np.concatenate((symbols[-int(filterSymbolLength/2):], symbols, symbols[:int(filterSymbolLength/2)]))

    """Zero-fill each symbol rather than repeating the symbol value to
    fill. This is to ensure the filter operates on an impulse response
    rather than a zero-order hold response."""
    iq = np.zeros(len(symbols) * saPerSym, dtype=np.complex)
    iq[::saPerSym] = symbols

    """Create pulse shaping filter. Taps should be an odd number to 
    ensure there is a tap in the center of the filter."""
    taps = filterSymbolLength * saPerSym + 1
    time, modFilter = filt(int(taps), alpha, symRate, fs)

    # Apply filter and trim off zeroed samples to ensure EXACT wraparound.
    iq = np.convolve(iq, modFilter)
    iq = iq[taps-1:-taps+1]

    # Scale waveform data
    sFactor = abs(np.amax(iq))
    iq = iq / sFactor * 0.707

    if zeroLast:
        iq[-1] = 0 + 1j*0

    return np.real(iq), np.imag(iq)


def multitone(fs=100e6, spacing=1e6, num=11, phase='random', cf=1e9, format='iq'):
    """Generates a multitone signal with given tone spacing, number of
    tones, sample rate, and phase relationship at baseband or RF."""
    if spacing * num > fs:
        raise error.WfmBuilderError('Multitone spacing and number of tones violates Nyquist.')

    # Determine start frequency based on parity of the number of tones
    if num % 2 != 0:
        # Freq offset is integer mult of spacing, so time can be 1/spacing
        f = - (num - 1) * spacing / 2
        time = 1 / spacing
    else:
        # Freq offset is integer mult of spacing/2, so time must be 2/spacing
        f = -num * spacing / 2 + spacing / 2
        time = 2 / spacing

    # Create time vector and record length
    t = np.linspace(-time / 2, time / 2, int(time * fs), endpoint=False)
    rl = len(t)

    # Define phase relationship
    if phase == 'random':
        phase = np.random.random_sample(size=rl) * 360
    elif phase == 'zero':
        phase = np.zeros(num)
    elif phase == 'increasing':
        phase = 180 * np.linspace(-1, 1, rl, endpoint=False)
    elif phase == 'parabolic':
        phase = np.cumsum(180 * np.linspace(-1, 1, rl, endpoint=False))

    if format.lower() == 'iq':
        # Preallocate 2D array for tones
        tones = np.zeros((num, len(t)), dtype=np.complex)

        # Create tones at each frequency and sum all together
        for n in range(num):
            tones[n] = np.exp(2j * np.pi * f * (t + phase[n]))
            f += spacing
        iq = tones.sum(axis=0)

        # Normalize and return values
        sFactor = abs(np.amax(iq))
        iq = iq / sFactor * 0.707

        return np.real(iq), np.imag(iq)
    elif format.lower() == 'real':
        # Preallocate 2D array for tones
        tones = np.zeros((num, len(t)))

        # Create tones at each frequency and sum all together
        for n in range(num):
            tones[n] = np.cos(2 * np.pi * (cf + f) * (t + phase[n]))
            f += spacing
        real = tones.sum(axis=0)

        # Normalize and return values
        sFactor = abs(np.amax(real))
        real = real / sFactor

        return real
    else:
        raise error.WfmBuilderError('Invalid waveform format selected. Choose "iq" or "real".')


def iq_correction(i, q, inst, vsaIPAddress='127.0.0.1', vsaHardware='"Analyzer1"',
                  cf=1e9, osFactor=4, thresh=0.4, convergence=2e-8):
    """Creates a 16-QAM signal from a signal generator at a
    user-selected center frequency and sample rate. Symbol rate and
    effective bandwidth of the calibration signal is determined by
    the oversampling rate in VSA. Creates a VSA instrument, which
    receives the 16-QAM signal and extracts & inverts an equalization
    filter and applies it to the user-defined waveform."""

    if osFactor not in [2, 4, 5, 10, 20]:
        raise ValueError('Oversampling factor invalid. Choose 2, 4, 5, 10, or 20.')

    # Use M8190A baseband sample rate if present
    if hasattr(inst, 'bbfs'):
        fs = inst.bbfs
    else:
        fs = inst.fs

    # Create, load, and play calibration signal
    symRate = fs / osFactor
    iCal, qCal = digmod_prbs_generator(fs=fs, modType='qam16', symRate=symRate)
    wfmId = inst.download_iq_wfm(iCal, qCal)
    inst.play(wfmId)

    # Connect to VSA
    vsa = communications.SocketInstrument(vsaIPAddress, 5025)
    vsa.write('*rst')
    vsa.query('*opc?')
    hwList = vsa.query('system:vsa:hardware:configuration:catalog?').split(',')
    if vsaHardware not in hwList:
        raise ValueError('Selected hardware not present in VSA hardware list.')
    vsa.write(f'system:vsa:hardware:configuration:select {vsaHardware}')
    vsa.query('*opc?')

    # Configure basic settings
    vsa.write('measure:nselect 1')
    vsa.write('measure:configure ddemod')
    vsa.write('trace1:data:name "Error Vector Time1"')
    vsa.write('trace3:data:name "Eq Impulse Response1"')
    vsa.write('format:trace:data real64')  # This is float64/double, not int64
    vsa.write(f'sense:frequency:center {cf}')
    vsa.write('input:analog:range:auto')
    vsa.write('display:layout 2, 2')

    # Configure digital demod parameters and enable equalizer
    vsa.write(f'ddemod:mod "Qam16"')
    vsa.write(f'ddemod:srate {symRate}')
    vsa.write(f'ddemod:symbol:points {osFactor}')
    vsa.write('ddemod:filter "RootRaisedCosine"')
    vsa.write('ddemod:filter:abt 0.35')
    vsa.write(f'ddemod:compensate:equalize:convergence {convergence}')
    vsa.write('ddemod:compensate:equalize 1')

    # Acquire data until EVM drops below a certain threshold
    evm = 100
    vsa.write('initiate:continuous off')
    while evm > thresh:
        vsa.write('initiate:immediate')
        vsa.query('*opc?')
        evm = float(vsa.query('trace4:data:table? "EvmRms"').strip())

    vsa.write('trace3:format "IQ"')
    vsa.write('trace3:data:x?')
    eqI = vsa.binblockread(dtype=np.float64).byteswap()
    vsa.write('trace3:data:y?')
    eqQ = vsa.binblockread(dtype=np.float64).byteswap()
    vsa.write('ddemod:compensate:equalize 0')

    vsa.err_check()
    inst.err_check()

    # Invert the phase of the equalizer impulse response
    equalizer = np.array(eqI - eqQ*1j)

    # Pseudo circular convolution to mitigate zeroing of samples due to filter delay
    rawIQ = np.array(i + q*1j)
    taps = len(equalizer)
    circIQ = np.concatenate((rawIQ[-int(taps / 2):], rawIQ, rawIQ[:int(taps / 2)]))

    # Apply filter, trim off delayed samples, and normalize
    iq = np.convolve(equalizer, circIQ)
    iq = iq[taps-1:-taps+1]
    sFactor = abs(np.amax(iq))
    iq = iq / sFactor * 0.707

    vsa.write('*rst')
    vsa.disconnect()

    iCorr = iq.real
    qCorr = iq.imag

    return iCorr, qCorr
