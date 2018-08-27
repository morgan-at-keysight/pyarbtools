"""
Instrument Control Class for Keysight AWGs
Author: Morgan Allison
Updated: 06/18
Builds instrument specific classes for each AWG. The classes include minimum
waveform length/granularity checks, binary waveform formatting, sequencer
length/granularity checks, sample rate checks, etc. per AWG.
Uses socket_instrument.py for instrument communication.
Python 3.6.4
Tested on M8190A
"""

from socket_instrument import *


class AwgError(Exception):
    """AWG Exception class"""


class VsgError(Exception):
    """Signal Generator Exception class"""


class M8190A(SocketInstrument):
    """Generic class for controlling a Keysight M8190A AWG."""

    def __init__(self, host, port=5025, timeout=3, reset=False):
        super().__init__(host, port, timeout)
        print(self.instId)
        if reset:
            self.write('*rst')
            self.query('*opc?')
            self.write('abort')
        self.fs = float(self.query('frequency:raster?').strip())
        self.res = self.query('trace1:dwidth?').strip().lower()
        self.func1 = self.query('func1:mode?').strip()
        self.func2 = self.query('func2:mode?').strip()
        self.out1 = self.query('output1:route?').strip()
        self.out2 = self.query('output2:route?').strip()
        self.cf1 = float(self.query('carrier1:freq?').strip().split(',')[0])
        self.cf2 = float(self.query('carrier2:freq?').strip().split(',')[0])
        self.refSrc = self.query('roscillator:source?').strip()
        self.refFreq = float(self.query('roscillator:frequency?').strip())

    def sanity_check(self):
        """Prints out initialized values."""
        print('Sample rate:', self.fs)
        print('Resolution:', self.res)
        print(f'Output path 1: {self.out1}, Output path 2: {self.out2}')
        print(f'Carrier 1: {self.cf1} Hz, Carrier 2: {self.cf2}')
        print(f'Function 1: {self.func1}, Function 2: {self.func2}')
        print('Ref source:', self.refSrc)
        print('Ref frequency:', self.refFreq)

    def check_wfm(self, wfm):
        """Checks minimum size and granularity and returns waveform with
        appropriate binary formatting based on the chosen DAC resolution.

        See pages 273-274 in Keysight M8190A User's Guide (Edition 13.0,
        October 2017) for more info."""

        self.check_resolution()

        rl = len(wfm)
        if rl < self.minLen:
            raise AwgError(f'Waveform length: {rl}, must be at least {self.minLen}.')
        if rl % self.gran != 0:
            raise AwgError(f'Waveform must have a granularity of {self.gran}.')

        return np.array(self.binMult * wfm, dtype=np.int16) << self.binShift

    def configure(self, res='wsp', clkSrc='int', fs=7.2e9, refSrc='axi', refFreq=100e6, out1='dac', out2='dac', func1='arb', func2='arb', cf1=2e9, cf2=2e9):
        """Sets basic configuration for M8190A and populates class attributes accordingly."""
        self.write(f'trace1:dwidth {res}')
        self.res = self.query('trace1:dwidth?').strip().lower()

        self.write(f'frequency:raster:source {clkSrc}')
        self.clkSrc = self.query('frequency:raster:source?').strip().lower()

        if 'int' in self.clkSrc:
            self.write(f'frequency:raster {fs}')
            self.fs = float(self.query('frequency:raster?').strip())
        else:
            self.write(f'frequency:raster:external {fs}')
            self.fs = float(self.query('frequency:raster:external?').strip())

        self.write(f'output1:route {out1}')
        self.out1 = self.query('output1:route?').strip()

        self.write(f'func1:mode {func1}')
        self.func1 = self.query('func1:mode?').strip()

        self.write(f'carrier1:freq {cf1}')
        self.cf1 = float(self.query('carrier1:freq?').strip().split(',')[0])

        self.write(f'output2:route {out2}')
        self.out2 = self.query('output2:route?').strip()

        self.write(f'func2:mode {func2}')
        self.func2 = self.query('func2:mode?').strip()

        self.write(f'carrier2:freq {cf2}')
        self.cf2 = float(self.query('carrier2:freq?').strip().split(',')[0])

        self.write(f'roscillator:source {refSrc}')
        self.refSrc = self.query('roscillator:source?').strip()

        self.write(f'roscillator:frequency {refFreq}')
        self.refFreq = float(self.query('roscillator:frequency?').strip())

        self.check_resolution()
        self.err_check()

    def set_resolution(self, res='wsp'):
        """Sets and reads resolution based on user input."""
        self.write(f'trace1:dwidth {res}')
        self.res = self.query('trace1:dwidth?').strip().lower()
        self.check_resolution()

    def iq_wfm_combiner(self, i, q):
        """Combines i and q wfms into a single wfm for download to AWG."""
        iq = np.empty(2 * len(i), dtype=np.int16)
        iq[0::2] = i
        iq[1::2] = q
        return iq

    def check_resolution(self):
        """Populates gran, minLen, binMult, & binShift, plus intFactor &
        idleGran if using DUC."""

        if self.res == 'wpr':
            self.gran = 48
            self.minLen = 240
            self.binMult = 8191
            self.binShift = 2
        elif self.res == 'wsp':
            self.gran = 64
            self.minLen = 320
            self.binMult = 2047
            self.binShift = 4
        elif 'intx' in self.res:
            # Granularity, min length, and binary format are the same for all interpolated modes.
            self.gran = 24
            self.minLen = 120
            self.binMult = 16383
            self.binShift = 1
            self.intFactor = int(self.res.split('x')[-1])
            if self.intFactor == 3:
                self.idleGran = 8
            elif self.intFactor == 12:
                self.idleGran = 2
            elif self.intFactor == 24 or self.intFactor == 48:
                self.idleGran = 1
        else:
            raise AwgError('Invalid resolution selected.')

    def download_wfm(self, wfm, ch=1):
        """Defines and downloads a waveform into the segment memory."""
        wfm = self.check_wfm(wfm)
        length = len(wfm)

        segIndex = int(self.query(f'trace{ch}:catalog?').strip().split(',')[-2]) + 1
        self.write(f'trace{ch}:def {segIndex}, {length}')
        self.binblockwrite(f'trace{ch}:data {segIndex}, 0, ', wfm)

    def download_iq_wfm(self, i, q, ch=1):
        """Defines and downloads an iq waveform into the segment memory."""
        i = self.check_wfm(i)
        q = self.check_wfm(q)
        iq = self.iq_wfm_combiner(i, q)
        length = len(iq) / 2

        segIndex = int(self.query(f'trace{ch}:catalog?').strip().split(',')[-2]) + 1
        self.write(f'trace{ch}:def {segIndex}, {length}')
        self.binblockwrite(f'trace{ch}:data {segIndex}, 0, ', iq)


class M8195A(SocketInstrument):
    """Generic class for controlling Keysight M8195A AWG."""

    def __init__(self, host, port=5025, timeout=3, reset=False):
        super().__init__(host, port, timeout)
        print(self.instId)
        if reset:
            self.write('*rst')
            self.query('*opc?')
        self.dacMode = self.query('inst:dacm?').strip()
        self.fs = float(self.query('frequency:raster?').strip())
        self.func = self.query('func:mode?').strip()
        self.refSrc = self.query('roscillator:source?').strip()
        self.refFreq = float(self.query('roscillator:frequency?').strip())
        self.gran = 256
        self.minLen = 256
        self.binMult = 127
        self.binShift = 0

    def sanity_check(self):
        """Prints out initialized values."""
        print('Sample rate:', self.fs)
        print('DAC Mode:', self.dacMode)
        print('Function:', self.func)
        print('Ref source:', self.refSrc)
        print('Ref frequency:', self.refFreq)

    def check_wfm(self, wfm):
        """Checks minimum size and granularity and returns waveform with
        appropriate binary formatting based on the chosen DAC resolution.

        See pages 273-274 in Keysight M8195A User's Guide (Edition 13.0,
        October 2017) for more info."""

        rl = len(wfm)
        if rl < self.minLen:
            raise AwgError(f'Waveform length: {rl}, must be at least {self.minLen}.')
        if rl % self.gran != 0:
            raise AwgError(f'Waveform must have a granularity of {self.gran}.')

        return np.array(self.binMult * wfm, dtype=np.int8) << self.binShift

    def configure(self, dacMode='single', fs=64e9, refSrc='axi', refFreq=100e6, func='arb'):
        """Sets basic configuration for M8195A and populates class attributes accordingly."""
        self.write(f'inst:dacm {dacMode}')
        self.dacMode = self.query('inst:dacm?').strip().lower()

        self.write(f'frequency:raster {fs}')
        self.fs = float(self.query('frequency:raster?').strip())

        self.write(f'func:mode {func}')
        self.func = self.query('func:mode?').strip()

        self.write(f'roscillator:source {refSrc}')
        self.refSrc = self.query('roscillator:source?').strip()

        self.write(f'roscillator:frequency {refFreq}')
        self.refFreq = float(self.query('roscillator:frequency?').strip())

        self.err_check()

    def download_wfm(self, wfm, ch=1):
        """Defines and downloads a waveform into the segment memory."""
        wfm = self.check_wfm(wfm)
        length = len(wfm)

        segIndex = int(self.query(f'trace{ch}:catalog?').strip().split(',')[-2]) + 1
        self.write(f'trace{ch}:def {segIndex}, {length}')
        self.binblockwrite(f'trace{ch}:data {segIndex}, 0, ', wfm)


class VSG(SocketInstrument):
    def __init__(self, host, port=5025, timeout=5, reset=False):
        """Generic class for controlling the EXG, MXG, and PSG family
        signal generators."""

        super().__init__(host, port, timeout)
        print(self.instId)
        if reset:
            self.write('*rst')
            # self.query('*opc?')
        self.rfState = self.query('output?').strip()
        self.modState = self.query('output:modulation?').strip()
        self.cf = float(self.query('frequency?').strip())
        self.amp = float(self.query('power?').strip())
        self.refSrc = self.query('roscillator:source?').strip()
        self.arbState = float(self.query('radio:arb:state?').strip())
        self.fs = float(self.query('radio:arb:sclock:rate?').strip())
        if 'int' in self.refSrc.lower():
            self.refFreq = 10e6
        elif 'ext' in self.refSrc.lower():
            self.refFreq = float(self.query('roscillator:frequency:external?').strip())
        elif 'bbg' in self.refSrc.lower():
            self.refFreq = float(self.query('roscillator:frequency:bbg?').strip())
        else:
            raise VsgError('Unknown refSrc selected.')
        self.gran = 2
        self.minLen = 60
        self.binMult = 32767

    def configure(self, rfState=0, modState=0, cf=1e9, amp=-130, iqScale=70, refSrc='int', refFreq=10e6, fs=200e6):
        """Sets basic configuration for VSG and populates class attributes accordingly."""
        self.write(f'output {rfState}')
        self.rfState = self.query('output?').strip()
        self.write(f'output:modulation {modState}')
        self.modState = self.query('output:modulation?').strip()
        self.write(f'frequency {cf}')
        self.cf = float(self.query('frequency?').strip())
        self.write(f'power {amp}')
        self.amp = float(self.query('power?').strip())
        self.write(f'roscillator:source {refSrc}')
        self.refSrc = self.query('roscillator:source?').strip()
        if 'int' in self.refSrc.lower():
            self.refFreq = 10e6
        elif 'ext' in self.refSrc.lower():
            self.refFreq = float(self.query('roscillator:frequency:external?').strip())
        elif 'bbg' in self.refSrc.lower():
            self.refFreq = float(self.query('roscillator:frequency:bbg?').strip())
        else:
            raise VsgError('Unknown refSrc selected.')
        self.write(f'radio:arb:sclock:rate {fs}')
        self.fs = float(self.query('radio:arb:sclock:rate?').strip())
        self.write(f'radio:arb:rscaling {iqScale}')
        self.iqScale = float(self.query('radio:arb:rscaling?').strip())

        # Arb state can only be turned on after a waveform has been loaded/selected
        # self.write(f'radio:arb:state {arbState}')
        # self.arbState = self.query('radio:arb:state?').strip()
        self.err_check()

    def sanity_check(self):
        """Prints out initialized values."""
        print('RF State:', self.rfState)
        print('Modulation State:', self.modState)
        print('Center Frequency:', self.cf)
        print('Output Amplitude:', self.amp)
        print('Reference source:', self.refSrc)
        print('Internal Arb State:', self.arbState)
        print('Internal Arb Sample Rate:', self.fs)
        print('IQ Scaling:', self.iqScale)

    def download_iq_wfm(self, name, i, q):
        """Defines and downloads an iq waveform into the segment memory."""
        i = self.check_wfm(i)
        q = self.check_wfm(q)
        iq = self.iq_wfm_combiner(i, q)

        self.binblockwrite(f'mmemory:data "wfm1:{name}", ', iq)
        self.write(f'radio:arb:waveform "WFM1:{name}"')

    def iq_wfm_combiner(self, i, q):
        """Combines i and q wfms into a single wfm for download to internal arb."""
        iq = np.empty(2 * len(i), dtype=np.int16)
        iq[0::2] = i
        iq[1::2] = q
        return iq

    def check_wfm(self, wfm, bigEndian=True):
        """Checks minimum size and granularity and returns waveform with
        appropriate binary formatting. Note that sig gens expect big endian
        byte order.

        See pages 205-256 in Keysight X-Series Signal Generators Programming
        Guide (November 2014 Edition) for more info."""

        rl = len(wfm)
        if rl < self.minLen:
            raise VsgError(f'Waveform length: {rl}, must be at least {self.minLen}.')
        if rl % self.gran != 0:
            # vsg.query('*opc?')
            raise VsgError(f'Waveform must have a granularity of {self.gran}.')

        if bigEndian:
            return np.array(self.binMult * wfm, dtype=np.int16).byteswap()
        else:
            return np.array(self.binMult * wfm, dtype=np.int16)


class UXG(SocketInstrument):
    def __init__(self, host, port=5025, timeout=5, reset=False):
        super().__init__(host, port, timeout)
        print(self.instId)
        if reset:
            self.write('*rst')
        self.rfState = self.query('output?').strip()
        self.modState = self.query('output:modulation?').strip()
        self.cf = float(self.query('frequency?').strip())
        self.amp = float(self.query('power?').strip())
        self.mode = self.query('instrument:select?').strip()
        self.fs = float(self.query('radio:arb:sclock:rate?').strip())
        self.gran = int(self.query('radio:arb:information:quantum?').strip())
        self.minLen = int(self.query('radio:arb:information:slength:minimum?').strip())
        self.binMult = 32767

    def configure(self, rfState=0, modState=0, cf=1e9, amp=-130, iqScale=70, refSrc='int',
                  refFreq=10e6, fs=200e6):
        self.write(f'output {rfState}')
        self.rfState = self.query('output?').strip()
        self.write(f'output:modulation {modState}')
        self.modState = self.query('output:modulation?').strip()
        self.write(f'frequency {cf}')
        self.cf = float(self.query('frequency?').strip())
        self.write(f'power {amp}')
        self.amp = float(self.query('power?').strip())
        self.write(f'roscillator:source {refSrc}')
        self.refSrc = self.query('roscillator:source?').strip()
        if 'int' in self.refSrc.lower():
            self.refFreq = 10e6
        elif 'ext' in self.refSrc.lower():
            self.refFreq = float(self.query('roscillator:frequency:external?').strip())
        elif 'bbg' in self.refSrc.lower():
            self.refFreq = float(self.query('roscillator:frequency:bbg?').strip())
        else:
            raise VsgError('Unknown refSrc selected.')
        self.write(f'radio:arb:sclock:rate {fs}')
        self.fs = float(self.query('radio:arb:sclock:rate?').strip())
        self.write(f'radio:arb:rscaling {iqScale}')
        self.iqScale = float(self.query('radio:arb:rscaling?').strip())

        self.err_check()

    def csv_pdw_file_download(self, fileName, fields=['Operation', 'Time'], data=[[1, 0], [2, 100e-6]]):
        """Builds a CSV PDW file, sends it into the UXG, and converts it to a binary PDW file."""
        # Write header fields separated by commas and terminated with \n
        pdwCsv = ','.join(fields) + '\n'
        for row in data:
            # Write subsequent rows with data values separated by commas and terminated with \n
            # The .join() function requires a list of strings, so convert numbers in row to strings
            rowString = ','.join([f'{r}' for r in row]) + '\n'
            pdwCsv += rowString

        # with open(f'{getcwd()}\\{fileName}.csv', 'w') as f:
        #     f.write(pdwCsv)

        self.write(f'memory:delete "{fileName}.csv"')
        self.binblockwrite(f'memory:data "{fileName}.csv", ', pdwCsv.encode('utf-8'))

        """Note: memory:import:stream imports/converts csv to pdw AND
        assigns the resulting pdw and waveform index files as the stream
        source. There is no need to send the stream:source:file or 
        stream:source:file:name commands because they are sent
        implicitly by memory:import:stream."""
        self.write(f'memory:import:stream "{fileName}.csv", "{fileName}"')
        self.query('*opc?')

    def download_matlab_wfm(self, fileName, zeroLast=False):
        """Imports a .mat file built in iqtools and formats it
        appropriately for transfer to UXG."""

        # Extract the file name from the full path and remove .mat extension
        name = fileName.split('\\')[-1].replace('.mat', '')

        # Load the iqdata member of the .mat structure
        iq = io.loadmat(fileName)['iqdata']

        # Zero the last sample to ensure 'Hold' pdw field behaves well
        if zeroLast:
            iq[-1] = 0

        # Split I and Q and download waveform
        i = np.real(iq).reshape(iq.shape[0])
        q = np.imag(iq).reshape(iq.shape[0])
        self.download_iq_wfm(name, i, q)

    def sanity_check(self):
        """Prints out initialized values."""
        self.err_check()
        print('RF State:', self.rfState)
        print('Modulation State:', self.modState)
        print('Center Frequency:', self.cf)
        print('Output Amplitude:', self.amp)
        print('Reference source:', self.refSrc)
        print('Internal Arb Sample Rate:', self.fs)
        print('IQ Scaling:', self.iqScale)

    def download_iq_wfm(self, name, i, q, assign=True):
        """Formats, downloads, and assigns an iq waveform into arb memory."""
        i = self.check_wfm(i)
        q = self.check_wfm(q)
        iq = self.iq_wfm_combiner(i, q)
        self.binblockwrite(f'memory:data "WFM1:{name}", ', iq)
        if assign:
            self.write(f'radio:arb:waveform "WFM1:{name}"')

    def iq_wfm_combiner(self, i, q):
        """Combines i and q wfms into a single wfm for download to AWG."""
        iq = np.empty(2 * len(i), dtype=np.uint16)
        iq[0::2] = i
        iq[1::2] = q
        return iq

    def check_wfm(self, wfm, bigEndian=True):
        """Checks minimum size and granularity and returns waveform with
        appropriate binary formatting. Note that sig gens expect big endian
        byte order.

        See pages 205-256 in Keysight X-Series Signal Generators Programming
        Guide (November 2014 Edition) for more info."""

        rl = len(wfm)
        if rl < self.minLen:
            raise VsgError(f'Waveform length: {rl}, must be at least {self.minLen}.')
        if rl % self.gran != 0:
            raise VsgError(f'Waveform must have a granularity of {self.gran}.')

        if bigEndian:
            return np.array(self.binMult * wfm, dtype=np.uint16).byteswap()
        else:
            return np.array(self.binMult * wfm, dtype=np.uint16)


def vsg_example(ipAddress):
    """Simple example script that creates either a chirp or barker pulse,
    and downloads, assigns, and plays out the waveform."""

    vsg = VSG(ipAddress, port=5025, reset=True)
    vsg.configure(rfState=1, modState=1, amp=-20, fs=50e6, iqScale=70)
    vsg.sanity_check()

    # name = 'barker'
    # length = 100e-6
    # code = 'b13'
    # i, q = barker_generator(length, vsg.fs, code)

    name = 'chirp'
    length = 100e-6
    bw = 40e6
    i, q = chirp_generator(length, vsg.fs, bw)

    i = np.append(i, np.zeros(5000))
    q = np.append(q, np.zeros(5000))
    vsg.write('mmemory:delete:wfm')
    vsg.download_iq_wfm(name, i, q)
    print(vsg.query('mmemory:catalog? "WFM1:"'))
    vsg.write('radio:arb:state on')
    vsg.err_check()


def m8190a_example(ipAddress):
    """Simple example script that sets up the digital upconverter on the
    M8190A and creates, downloads, assigns, and plays back a simple IQ
    waveform from the AC port."""

    awg = M8190A(ipAddress, port=5025, reset=True)
    awg.configure(res='intx3', cf1=1e9)
    awg.sanity_check()
    # wfm = np.sin(np.linspace(0, 2 * np.pi, 2400))
    i = np.ones(awg.minLen, dtype=np.int16)
    q = np.zeros(awg.minLen, dtype=np.int16)
    awg.download_iq_wfm(i, q)
    awg.write('trace:select 1')
    awg.write('output1:route ac')
    awg.write('output1:norm on')
    awg.write('init:imm')
    awg.query('*opc?')
    awg.err_check()
    awg.disconnect()


def uxg_example(ipAddress):
    """Simple example script that creates and downloads a chirp waveform,
    defines a very simple pdw csv file, and loads that pdw file into the
    UXG and plays it out."""

    """NOTE: trigger settings may need to be adjusted for continuous
    output. This will be fixed in a future release."""

    uxg = UXG(ipAddress, port=5025, timeout=10, reset=False)
    uxg.err_check()

    # Create IQ waveform
    length = 1e-6
    fs = 250e6
    chirpBw = 100e6
    i, q = chirp_generator(length, fs, chirpBw)
    wfmName = '1US_100MHz_CHIRP'
    uxg.download_iq_wfm(wfmName, i, q)

    # Define and generate csv pdw file
    uxg.write('stream:state off')
    pdwName = 'basic_chirp'
    fields = ['Operation', 'Time', 'Frequency', 'Zero/Hold', 'Markers', 'Name']
    data = [[1, 0, 1e9, 'Hold', '0x1', wfmName],
            [2, 10e-6, 1e9, 'Hold', '0x0', wfmName]]

    uxg.csv_pdw_file_download(pdwName, fields, data)
    uxg.write('stream:state on')

    uxg.err_check()
    uxg.disconnect()


def chirp_generator(length=100e-6, fs=100e6, chirpBw=20e6):
    """Generates a symmetrical linear chirp at baseband. Chirp direction
    is determined by the sign of chirpBw (pos = up chirp, neg = down chirp)."""

    """Define baseband iq waveform. Create a time vector that goes from
    -1/2 to 1/2 instead of 0 to 1. This ensures that the chirp will be
    symmetrical around the carrier."""

    rl = fs * length
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
    i = np.real(iq)
    q = np.imag(iq)

    return i, q


def barker_generator(length=100e-6, fs=100e6, code='b2'):
    """Generates a baseband Barker phase coded signal."""

    # Codes taken from https://en.wikipedia.org/wiki/Barker_code
    barkerCodes = {'b2': [1, -1], 'b3': [1, 1, -1],
                   'b4': [1, 1, -1, 1], 'b4alt': [1, 1, 1, -1],
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
    i = np.real(iq)
    q = np.imag(iq)

    return i, q


def main():
    # m8190a_example('141.121.210.171')
    vsg_example('10.112.180.242')


if __name__ == '__main__':
    main()
