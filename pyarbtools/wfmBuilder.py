"""
pyarbtools 0.1.0
wfmBuilder
Author: Morgan Allison
Updated: 10/18
Provides generic waveform creation capabilities for pyarbtools.
"""

import nnresample

import os
import numpy as np
from scipy.signal import max_len_seq
from pyarbtools import communications
from pyarbtools import instruments


def chirp_generator(length=100e-6, fs=100e6, chirpBw=20e6, zeroLast=False):
    """Generates a symmetrical linear chirp at baseband. Chirp direction
    is determined by the sign of chirpBw (pos=up chirp, neg=down chirp)."""

    """Define baseband iq waveform. Create a time vector that goes from
    -1/2 to 1/2 instead of 0 to 1. This ensures that the chirp will be
    symmetrical around the carrier."""

    rl = int(fs * length)
    chirpRate = chirpBw / length
    t = np.linspace(-rl / fs / 2, rl / fs / 2, rl, endpoint=False)

    """Direct phase manipulation was used to create the chirp modulation.
    https://en.wikipedia.org/wiki/Chirp#Linear
    phase = 2*pi*(f0*t + k/2*t^2)
    Since this is a baseband modulation scheme, there is no f0 term and the
    factors of 2 cancel out. It looks odd to have a pi multiplier rather than
    2*pi, but the math works out correctly. Just throw that into the complex
    exponential function and you're off to the races."""

    mod = np.pi * chirpRate * t**2
    iq = np.exp(1j * mod)
    if zeroLast:
        iq[-1] = 0 + 1j*0
    i = np.real(iq)
    q = np.imag(iq)

    return i, q


def barker_generator(length=100e-6, fs=100e6, code='b2', zeroLast=False):
    """Generates a baseband Barker phase coded signal."""

    # Codes taken from https://en.wikipedia.org/wiki/Barker_code
    barkerCodes = {'b2': [1, -1], 'b3': [1, 1, -1],
                   'b41': [1, 1, -1, 1], 'b42': [1, 1, 1, -1],
                   'b5': [1, 1, 1, -1, 1], 'b7': [1, 1, 1, -1, -1, 1, -1],
                   'b11': [1, 1, 1, -1, -1, -1, 1, -1, -1, 1, -1],
                   'b13': [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1]}

    # Create array for each phase shift and concatenate them
    codeSamples = int(length / len(barkerCodes[code]) * fs)
    barker = []
    for p in barkerCodes[code]:
        temp = np.full((codeSamples,), p)
        barker = np.concatenate([barker, temp])

    mod = np.pi / 2 * barker
    iq = np.exp(1j * mod)

    if zeroLast:
        iq[-1] = 0 + 0j
    i = np.real(iq)
    q = np.imag(iq)

    return i, q


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


def digmod_prbs_generator(modType, fs, symRate, prbsOrder=9, filt=rrc_filter, alpha=0.35):
    """Generates a baseband modulated signal with a given modulation
    type and root raised cosine filter using PRBS data."""

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
    elif modType.lower() == 'qam16':
        bitsPerSym = 4
        modulator = qam16_modulator
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

    return np.real(iq), np.imag(iq)


def iq_correction(i, q, instrument, vsaIPAddress='127.0.0.1', vsaHardware='"Analyzer1"', cf=1e9, bw=40e6):
    """Creates a 16-QAM signal from a signal generator at a
    user-selected center frequency, bandwidth, and sample rate.
    Creates a VSA instrument, which receives the 16-QAM signal and
    extracts an equalization filter and applies it to the
    user-defined waveform."""

    i, q = digmod_prbs_generator('qam16', instrument.bbfs, bw)
    saPerSym = instrument.bbfs / bw
    instrument.download_iq_wfm(i, q)
    # Add .play() method to each instrument class, for now use M8190A
    instrument.write('trace:select 1')
    instrument.write('output1:route ac')
    instrument.write('output1:norm on')
    instrument.write('init:cont on')
    instrument.write('init:imm')
    instrument.query('*opc?')

    vsa = communications.SocketInstrument(vsaIPAddress, 5025)
    print(vsa.query('*idn?'))
    vsa.write('*rst')
    vsa.query('*opc?')
    hwList = vsa.query('system:vsa:hardware:configuration:catalog?')
    hwList = hwList.split(',')
    if vsaHardware not in hwList:
        raise ValueError('Selected hardware not present in VSA hardware list.')
    vsa.write(f'system:vsa:hardware:configuration:select {vsaHardware}')
    vsa.query('*opc?')

    vsa.write('measure:nselect 1')
    vsa.write('measure:configure ddemod')
    vsa.write('trace3:data:name "Eq Impulse Response1"')
    vsa.write('format:trace:data real64')  # This is float64/double, not int64
    vsa.write(f'sense:frequency:center {cf}')
    vsa.write(f'sense:frequency:span {bw * 1.35}')
    vsa.write('input:analog:range:auto')
    vsa.write('display:layout 2, 2')
    vsa.query('*opc?')
    vsaFs = int(vsa.query("frequency:srate?").strip())

    # Configure digital demod parameters
    vsa.write(f'ddemod:mod "Qam16"')
    vsa.write(f'ddemod:srate {bw}')
    vsa.write('ddemod:filter "RootRaisedCosine"')
    vsa.write('ddemod:filter:abt 0.35')
    eqSaPerSym = float(vsa.query('ddemod:symbol:points?').strip())
    symRate = float(vsa.query('ddemod:srate?').strip())
    eqLength = int(vsa.query('ddemod:compensate:equalize:length?').strip())
    print(symRate/eqSaPerSym)
    vsa.write('ddemod:compensate:equalize 1')

    # Acquire data until EVM drops below a certain threshold
    evm = 100
    while evm > 0.6:
        vsa.write('initiate:continuous off')
        vsa.write('initiate:immediate')
        vsa.query('*opc?')
        evm = float(vsa.query('trace4:data:table? "EvmRms"').strip())

    fileName = os.getcwd() + '\\equalizer_taps.csv'
    vsa.write(f'mmemory:store:trace 2, "{fileName}", "CSV", 1')

    vsa.write('trace3:format "IQ"')
    vsa.write('trace3:data:x?')
    x = vsa.binblockread(dtype=np.float64).byteswap()
    vsa.write('trace3:data:y?')
    y = vsa.binblockread(dtype=np.float64).byteswap()
    vsa.write('ddemod:compensate:equalize 0')

    vsa.err_check()
    instrument.err_check()

    equalizer = np.array(x + y*1j)
    equalizer = nnresample.resample(equalizer, int(awg.bbfs), int(vsaFs))
    rawIQ = np.array(i + q*1j)

    """Perform a pseudo circular convolution on the symbols to mitigate
    zeroing of samples due to filter delay (i.e. PREpend the
    last few symbols and APpend the first few symbols)."""
    taps = len(equalizer)
    circIQ = np.concatenate((rawIQ[-int(taps / 2):], rawIQ, rawIQ[:int(taps / 2)]))
    # symbols = np.concatenate((symbols[-int(filterSymbolLength / 2):], symbols, symbols[:int(filterSymbolLength / 2)]))

    iq = np.convolve(circIQ, equalizer)
    iq = iq[taps-1:-taps+1]

    iCorr = iq.real
    qCorr = iq.imag

    # eqIQ = np.empty(2 * len(x))
    # eqIQ[0::2] = x
    # eqIQ[1::2] = y
    # with open(fileName, 'r') as f:
    #     raw = f.read()
    #     raw = raw.replace('\n', ',')
    #     raw = raw.split(',')[:-1]
    #     print(raw)
    # loadedIQ = [float(r) for r in raw]
    # for a, b in zip(nativeIQ, loadedIQ):
    #     print(a, b)

    return iCorr, qCorr



if __name__ == '__main__':
    awg = instruments.M8190A('141.121.210.241', reset=True)
    awg.configure('intx3', fs=7.2e9, out1='ac', cf1=1e9)
    i, q = digmod_prbs_generator('qam16', awg.bbfs, 100e6)

    iCorr, qCorr = iq_correction(i, q, awg, vsaHardware='"PXA M"', bw=100e6)

    import matplotlib.pyplot as plt
    plt.plot(iCorr)
    plt.plot(qCorr)
    plt.show()
    awg.download_iq_wfm(iCorr, qCorr)
    print(awg.query(f'trace:catalog?').strip())

    awg.write('abort')
    awg.write('trace:select 2')
    awg.write('init:cont on')
    awg.write('init:imm')
    print(awg.query('trace:select?'))
    awg.query('*opc?')
    awg.err_check()
