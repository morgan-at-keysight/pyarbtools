"""
instruments
Author: Morgan Allison, Keysight RF/uW Application Engineer
Builds instrument specific classes for each signal generator.
The classes include minimum waveform length/granularity checks, binary
waveform formatting, sequencer length/granularity checks, sample rate
checks, etc. per instrument.
Tested on M8190A, M8195A, M8196A,
N5182B, E8257D, M9383A, N5193A, N5194A
"""

"""
TODO:
* Add check to each instrument class to ensure that the correct 
    instrument is connected
* Add a function for IQ adjustments in VSG class
* Add multithreading for waveform download and wfmBuilder
* Separate out configure() into individual methods that update class attributes
* Add a check for PDW length (600k limit?)
* Add a multi-binblockwrite feature for download_wfm in the case of 
    waveform size > 1 GB
"""

import numpy as np
import math
from pyarbtools import communications
from pyarbtools import error


def wraparound_calc(length, gran, minLen):
    """Computes the number of times to repeat a waveform based on
    generator granularity requirements."""

    repeats = 1
    temp = length
    while temp % gran != 0 or temp < minLen:
        temp += length
        repeats += 1
    return repeats


class M8190A(communications.SocketInstrument):
    """Generic class for controlling a Keysight M8190A AWG."""

    def __init__(self, host, port=5025, timeout=10, reset=False):
        super().__init__(host, port, timeout)
        if reset:
            self.write('*rst')
            self.query('*opc?')
            self.write('abort')
        self.res = self.query('trace1:dwidth?').strip().lower()
        self.func1 = self.query('func1:mode?').strip()
        self.func2 = self.query('func2:mode?').strip()
        self.gran = 0
        self.minLen = 0
        self.binMult = 0
        self.binShift = 0
        self.intFactor = 1
        self.idleGran = 0
        self.clkSrc = self.query('frequency:raster:source?').strip().lower()
        self.fs = float(self.query('frequency:raster?').strip())
        self.bbfs = self.fs
        self.refSrc = self.query('roscillator:source?').strip()
        self.refFreq = float(self.query('roscillator:frequency?').strip())
        self.out1 = self.query('output1:route?').strip()
        self.out2 = self.query('output2:route?').strip()
        self.func1 = self.query('func1:mode?').strip()
        self.func2 = self.query('func2:mode?').strip()
        self.cf1 = float(self.query('carrier1:freq?').strip().split(',')[0])
        self.cf2 = float(self.query('carrier2:freq?').strip().split(',')[0])
        self.check_resolution()

    def sanity_check(self):
        """Prints out initialized values."""
        print('Sample rate:', self.fs)
        print('Baseband Sample Rate:', self.bbfs)
        print('Resolution:', self.res)
        print(f'Output path 1: {self.out1}, Output path 2: {self.out2}')
        print(f'Carrier 1: {self.cf1} Hz, Carrier 2: {self.cf2}')
        print(f'Function 1: {self.func1}, Function 2: {self.func2}')
        print('Ref source:', self.refSrc)
        print('Ref frequency:', self.refFreq)

    def configure(self, res='wsp', clkSrc='int', fs=7.2e9, refSrc='axi', refFreq=100e6, out1='dac',
                  out2='dac', func1='arb', func2='arb', cf1=1e9, cf2=1e9):
        """Sets basic configuration for M8190A and populates class attributes accordingly."""

        if not isinstance(fs, float) or fs <= 0:
            raise ValueError('Sample rate must be a positive floating point value.')
        if not isinstance(refFreq, float) or refFreq <= 0:
            raise ValueError('Reference frequency must be a positive floating point value.')
        if not isinstance(cf1, float) or cf1 <= 0 or not isinstance(cf2, float) or cf2 <= 0:
            raise error.SockInstError('Carrier frequencies must be positive floating point values.')

        self.write('abort')
        self.set_resolution(res)

        self.write(f'frequency:raster:source {clkSrc}')
        self.clkSrc = self.query('frequency:raster:source?').strip().lower()

        if 'int' in self.clkSrc:
            self.write(f'frequency:raster {fs}')
            self.fs = float(self.query('frequency:raster?').strip())
        else:
            self.write(f'frequency:raster:external {fs}')
            self.fs = float(self.query('frequency:raster:external?').strip())

        self.bbfs = self.fs / self.intFactor

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

        self.err_check()

    def set_resolution(self, res='wsp'):
        """Sets and reads resolution based on user input."""
        self.write(f'trace1:dwidth {res}')
        self.res = self.query('trace1:dwidth?').strip().lower()
        self.check_resolution()

    def check_resolution(self):
        """Populates gran, minLen, binMult, binShift, plus intFactor &
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
            self.bbfs = self.fs / self.intFactor
            if self.intFactor == 3:
                self.idleGran = 8
            elif self.intFactor == 12:
                self.idleGran = 2
            elif self.intFactor == 24 or self.intFactor == 48:
                self.idleGran = 1
        else:
            raise error.AWGError('Invalid resolution selected.')

    def download_wfm(self, wfmData, ch=1, name='wfm', wfmFormat='iq'):
        """Defines and downloads a waveform into the segment memory.
        Assigns a waveform name to the segment. Returns segment number."""

        self.write('abort')
        self.query('*opc?')
        if wfmFormat.lower() == 'iq':
            if wfmData.dtype != np.complex:
                raise TypeError('Invalid wfm type. IQ waveforms must be an array of complex values.')
            else:
                i = self.check_wfm(np.real(wfmData))
                q = self.check_wfm(np.imag(wfmData))

                wfm = self.iq_wfm_combiner(i, q)
                length = len(wfm) / 2
        elif wfmFormat.lower() == 'real':
            wfm = self.check_wfm(wfmData)
            length = len(wfm)

        segment = int(self.query(f'trace{ch}:catalog?').strip().split(',')[-2]) + 1
        self.write(f'trace{ch}:def {segment}, {length}')
        self.binblockwrite(f'trace{ch}:data {segment}, 0, ', wfm)
        self.write(f'trace{ch}:name {segment},"{name}_{segment}"')

        return segment

    # def download_iq_wfm(self, i, q, ch=1, name='wfm'):
    #     """Defines and downloads an IQ waveform into the segment memory.
    #     Optionally defines a waveform name. Returns useful waveform
    #     identifier."""
    #
    #     self.write('abort')
    #     self.query('*opc?')
    #     i = self.check_wfm(i)
    #     q = self.check_wfm(q)
    #
    #     iq = self.iq_wfm_combiner(i, q)
    #     length = len(iq) / 2
    #
    #     segment = int(self.query(f'trace{ch}:catalog?').strip().split(',')[-2]) + 1
    #     self.write(f'trace{ch}:def {segment}, {length}')
    #     self.binblockwrite(f'trace{ch}:data {segment}, 0, ', iq)
    #     self.write(f'trace{ch}:name {segment},"{name}_{segment}"')
    #
    #     return segment

    @staticmethod
    def iq_wfm_combiner(i, q):
        """Combines i and q wfms into a single interleaved wfm for download to AWG."""
        iq = np.empty(2 * len(i), dtype=np.int16)
        iq[0::2] = i
        iq[1::2] = q
        return iq

    def check_wfm(self, wfm):
        """Checks minimum size and granularity and returns waveform with
        appropriate binary formatting based on the chosen DAC resolution.

        See pages 273-274 in Keysight M8190A User's Guide (Edition 13.0,
        October 2017) for more info."""

        self.check_resolution()

        repeats = wraparound_calc(len(wfm), self.gran, self.minLen)
        wfm = np.tile(wfm, repeats)
        rl = len(wfm)
        if rl < self.minLen:
            raise error.AWGError(f'Waveform length: {rl}, must be at least {self.minLen}.')
        rem = rl % self.gran
        if rem != 0:
            raise error.GranularityError(f'Waveform must have a granularity of {self.gran}. Extra samples: {rem}')

        return np.array(self.binMult * wfm, dtype=np.int16) << self.binShift

    def delete_segment(self, wfmID=1, ch=1):
        """Deletes waveform segment"""
        if type(wfmID) != int or wfmID < 1:
            raise error.SockInstError('Segment ID must be a positive integer.')
        if ch not in [1, 2]:
            raise error.SockInstError('Channel must be 1 or 2.')
        self.write('abort')
        self.write(f'trace{ch}:delete {wfmID}')

    def clear_all_wfm(self):
        """Clears all segments from segment memory."""
        self.write('abort')
        self.write('trace1:delete:all')
        self.write('trace2:delete:all')

    def play(self, wfmID=1, ch=1):
        """Selects waveform, turns on analog output, and begins continuous playback."""
        self.write('abort')
        self.write(f'trace{ch}:select {wfmID}')
        self.write(f'output{ch}:norm on')
        self.write('init:cont on')
        self.write('init:imm')
        self.query('*opc?')

    def stop(self, ch=1):
        """Turns off analog output and stops playback."""
        self.write(f'output{ch}:norm off')
        self.write('abort')


class M8195A(communications.SocketInstrument):
    """Generic class for controlling Keysight M8195A AWG."""

    def __init__(self, host, port=5025, timeout=10, reset=False):
        super().__init__(host, port, timeout)
        if reset:
            self.write('*rst')
            self.query('*opc?')
        self.dacMode = self.query('inst:dacm?').strip()
        self.memDiv = 1
        self.fs = float(self.query('frequency:raster?').strip())
        self.effFs = self.fs / self.memDiv
        self.func = self.query('func:mode?').strip()
        self.refSrc = self.query('roscillator:source?').strip()
        self.refFreq = float(self.query('roscillator:frequency?').strip())
        self.gran = 256
        self.minLen = 256
        self.binMult = 127
        self.binShift = 0

    def configure(self, dacMode='single', memDiv=1, fs=64e9, refSrc='axi', refFreq=100e6, func='arb'):
        """Sets basic config uration for M8195A and populates class attributes accordingly."""
        if not isinstance(fs, float) or fs <= 0:
            raise ValueError('Sample rate must be a positive floating point value.')
        if not isinstance(refFreq, float) or refFreq <= 0:
            raise ValueError('Reference frequency must be a positive floating point value.')
        if memDiv not in [1, 2, 4]:
            raise ValueError('Memory divider must be 1, 2, or 4.')

        self.write(f'inst:dacm {dacMode}')
        self.dacMode = self.query('inst:dacm?').strip().lower()

        self.write(f'instrument:memory:extended:rdivider div{memDiv}')
        self.memDiv = int(self.query('instrument:memory:extended:rdivider?').strip().split('DIV')[-1])

        self.write(f'frequency:raster {fs}')
        self.fs = float(self.query('frequency:raster?').strip())
        self.effFs = self.fs / self.memDiv

        self.write(f'func:mode {func}')
        self.func = self.query('func:mode?').strip()

        self.write(f'roscillator:source {refSrc}')
        self.refSrc = self.query('roscillator:source?').strip()

        self.write(f'roscillator:frequency {refFreq}')
        self.refFreq = float(self.query('roscillator:frequency?').strip())

        self.err_check()

    def sanity_check(self):
        """Prints out initialized values."""
        print('Sample rate:', self.fs)
        print('DAC Mode:', self.dacMode)
        print('Function:', self.func)
        print('Ref source:', self.refSrc)
        print('Ref frequency:', self.refFreq)

    def download_wfm(self, wfm, ch=1, name='wfm'):
        """Defines and downloads a waveform into the segment memory.
        Assigns a waveform name to the segment. Returns segment number."""

        self.write('abort')
        wfm = self.check_wfm(wfm)
        length = len(wfm)

        segment = int(self.query(f'trace{ch}:catalog?').strip().split(',')[-2]) + 1
        self.write(f'trace{ch}:def {segment}, {length}')
        self.binblockwrite(f'trace{ch}:data {segment}, 0, ', wfm)
        self.write(f'trace{ch}:name {segment},"{name}_{segment}"')

        return segment

    def check_wfm(self, wfm):
        """Checks minimum size and granularity and returns waveform with
        appropriate binary formatting based on the chosen DAC resolution.

        See pages 273-274 in Keysight M8195A User's Guide (Edition 13.0,
        October 2017) for more info."""

        repeats = wraparound_calc(len(wfm), self.gran, self.minLen)
        wfm = np.tile(wfm, repeats)
        rl = len(wfm)
        if rl < self.minLen:
            raise error.AWGError(f'Waveform length: {rl}, must be at least {self.minLen}.')
        if rl % self.gran != 0:
            raise error.GranularityError(f'Waveform must have a granularity of {self.gran}.')

        return np.array(self.binMult * wfm, dtype=np.int8) << self.binShift

    def delete_segment(self, wfmID=1, ch=1):
        """Deletes waveform segment"""
        if type(wfmID) != int or wfmID < 1:
            raise error.SockInstError('Segment ID must be a positive integer.')
        if ch not in [1, 2, 3, 4]:
            raise error.SockInstError('Channel must be 1, 2, 3, or 4.')
        self.write('abort')
        self.write(f'trace{ch}:del {wfmID}')

    def clear_all_wfm(self):
        """Clears all segments from segment memory."""
        self.write('abort')
        for ch in range(1,5):
            self.write(f'trace{ch}:del:all')

    def play(self, wfmID=1, ch=1):
        """Selects waveform, turns on analog output, and begins continuous playback."""
        self.write(f'trace:select {wfmID}')
        self.write(f'output{ch} on')
        self.write('init:cont on')
        self.write('init:imm')

    def stop(self, ch=1):
        """Turns off analog output and stops playback."""
        self.write(f'output{ch} off')
        self.write('abort')


class M8196A(communications.SocketInstrument):
    """Generic class for controlling Keysight M8196A AWG."""

    def __init__(self, host, port=5025, timeout=10, reset=False):
        super().__init__(host, port, timeout)
        if reset:
            self.write('*rst')
            self.query('*opc?')
        self.dacMode = self.query('inst:dacm?').strip()
        self.fs = float(self.query('frequency:raster?').strip())
        self.amp = float(self.query('voltage?').strip())
        self.refSrc = self.query('roscillator:source?').strip()
        self.refFreq = float(self.query('roscillator:frequency?').strip())
        self.gran = 128
        self.minLen = 128
        self.maxLen = 524288
        self.binMult = 127
        self.binShift = 0

    def configure(self, dacMode='single', fs=92e9, refSrc='axi', refFreq=100e6):
        """Sets basic configuration for M8196A and populates class attributes accordingly."""
        # Built-in type and range checking for dacMode, fs, and amplitude

        if not isinstance(fs, float) or fs <= 0:
            raise ValueError('Sample rate must be a positive floating point value.')
        if not isinstance(refFreq, float) or refFreq <= 0:
            raise ValueError('Reference frequency must be a positive floating point value.')

        self.write(f'inst:dacm {dacMode}')
        self.dacMode = self.query('inst:dacm?').strip().lower()

        self.write(f'frequency:raster {fs}')
        self.fs = float(self.query('frequency:raster?').strip())

        # Check for valid refSrc arguments and assign
        if refSrc.lower() not in ['int', 'ext', 'axi']:
            raise error.AWGError('Invalid reference source selection.')
        self.write(f'roscillator:source {refSrc}')
        self.refSrc = self.query('roscillator:source?').strip().lower()

        # Check for presence of external ref signal
        srcAvailable = self.query(f'roscillator:source:check? {refSrc}').strip()
        if not srcAvailable:
            raise error.AWGError('No signal at selected reference source.')

        # Only set ref frequency if using ext ref, int/axi is always 100 MHz
        if self.refSrc == 'ext':
            # Seamlessly manage external clock range selection based on ref freq.
            # Precision clock source
            if 2.3125e9 <= refFreq <= 3e9:
                self.write('roscillator:range rang3')
            # Standard external clock source
            elif 10e6 <= refFreq <= 300e6:
                self.write('roscillator:range rang1')
            # Wide external clock source
            elif 162e6 <= refFreq <= 17e9:
                self.write('roscillator:range rang2')
            else:
                raise error.AWGError('Selected reference clock frequency outside allowable range.')
            self.write(f'roscillator:frequency {refFreq}')
        self.refFreq = float(self.query('roscillator:frequency?').strip())

        self.err_check()

    def sanity_check(self):
        """Prints out initialized values."""
        print('Sample rate:', self.fs)
        print('DAC Mode:', self.dacMode)
        print('Ref source:', self.refSrc)
        print('Ref frequency:', self.refFreq)

    def download_wfm(self, wfm, ch=1, name='wfm'):
        """Defines and downloads a waveform into the segment memory.
        Assigns a waveform name to the segment. Returns segment number."""

        self.write('abort')
        wfm = self.check_wfm(wfm)
        length = len(wfm)

        segment = int(self.query(f'trace{ch}:catalog?').strip().split(',')[-2]) + 1
        self.write(f'trace{ch}:def {segment}, {length}')
        self.binblockwrite(f'trace{ch}:data {segment}, 0, ', wfm)
        self.write(f'trace{ch}:name {segment},"{name}_{segment}"')

        return segment

    def check_wfm(self, wfm):
        """Checks minimum size and granularity and returns waveform with
        appropriate binary formatting based on the chosen DAC resolution.

        See page 132 in Keysight M8196A User's Guide (Edition 2.2,
        March 2018) for more info."""

        repeats = wraparound_calc(len(wfm), self.gran)
        wfm = np.tile(wfm, repeats)
        rl = len(wfm)
        if rl < self.minLen:
            raise error.AWGError(f'Waveform length: {rl}, must be at least {self.minLen}.')
        if rl > self.maxLen:
            raise error.AWGError(f'Waveform length: {rl}, must be shorter than {self.maxLen}.')
        if rl % self.gran != 0:
            raise error.GranularityError(f'Waveform must have a granularity of {self.gran}.')

        return np.array(self.binMult * wfm, dtype=np.int8) << self.binShift

    def play(self, ch=1):
        """Selects waveform, activates analog output, and begins continuous playback."""
        self.write(f'output{ch}:state on')
        self.write('init:cont on')
        self.write('init:imm')

    def stop(self, ch=1):
        """Turns off analog output and stops playback."""
        self.write('abort')
        self.write(f'output{ch}:state off')


class VSG(communications.SocketInstrument):
    def __init__(self, host, port=5025, timeout=10, reset=False):
        """Generic class for controlling the EXG, MXG, and PSG family
        signal generators."""

        super().__init__(host, port, timeout)
        if reset:
            self.write('*rst')
            self.query('*opc?')
        self.rfState = self.query('output?').strip()
        self.modState = self.query('output:modulation?').strip()
        self.cf = float(self.query('frequency?').strip())
        self.amp = float(self.query('power?').strip())
        self.alcState = self.query('power:alc?')
        self.refSrc = self.query('roscillator:source?').strip()
        self.arbState = self.query('radio:arb:state?').strip()
        self.fs = float(self.query('radio:arb:sclock:rate?').strip())

        if 'int' in self.refSrc.lower():
            self.refFreq = 10e6
        elif 'ext' in self.refSrc.lower():
            self.refFreq = float(self.query('roscillator:frequency:external?').strip())
        elif 'bbg' in self.refSrc.lower():
            if 'M938' not in self.instId:
                self.refFreq = float(self.query('roscillator:frequency:bbg?').strip())
            else:
                raise error.VSGError('Invalid reference source chosen, select \'int\' or \'ext\'.')
        else:
            raise error.VSGError('Unknown refSrc selected.')

        self.minLen = 60
        self.binMult = 32767
        if 'M938' not in self.instId:
            self.iqScale = float(self.query('radio:arb:rscaling?').strip())
            self.gran = 2
        else:
            self.gran = 4

    def configure(self, rfState=0, modState=0, cf=1e9, amp=-20, alcState=0, iqScale=70, refSrc='int', fs=200e6):
        """Sets basic configuration for VSG and populates class attributes accordingly."""
        if not isinstance(fs, float) or fs <= 0:
            raise ValueError('Sample rate must be a positive floating point value.')
        if not isinstance(cf, float) or cf <= 0:
            raise ValueError('Carrier frequency must be a positive floating point value.')
        if not isinstance(iqScale, int) or iqScale <= 0 or iqScale > 100:
            raise ValueError('iqScale argument must be an integer between 1 and 100.')
        if not isinstance(amp, int):
            raise ValueError('Amp argument must be an integer.')

        self.write(f'output {rfState}')
        self.rfState = int(self.query('output?').strip())
        self.write(f'output:modulation {modState}')
        self.modState = int(self.query('output:modulation?').strip())
        self.write(f'frequency {cf}')
        self.cf = float(self.query('frequency?').strip())
        self.write(f'power {amp}')
        self.amp = float(self.query('power?').strip())
        self.write(f'power:alc {alcState}')
        self.alcState = int(self.query('power:alc?').strip())
        self.write(f'roscillator:source {refSrc}')
        self.refSrc = self.query('roscillator:source?').strip()
        if 'int' in self.refSrc.lower():
            self.refFreq = 10e6
        elif 'ext' in self.refSrc.lower():
            self.refFreq = float(self.query('roscillator:frequency:external?').strip())
        elif 'bbg' in self.refSrc.lower():
            self.refFreq = float(self.query('roscillator:frequency:bbg?').strip())
        else:
            raise error.VSGError('Unknown refSrc selected.')
        self.write(f'radio:arb:sclock:rate {fs}')
        self.fs = float(self.query('radio:arb:sclock:rate?').strip())

        # M9381/3A don't have an IQ scaling command
        if 'M938' not in self.instId:
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
        print('ALC state:', self.alcState)
        print('Reference Source:', self.refSrc)
        print('Internal Arb State:', self.arbState)
        print('Internal Arb Sample Rate:', self.fs)
        if 'M938' not in self.instId:
            print('IQ Scaling:', self.iqScale)

    def download_wfm(self, wfmData, wfmID='wfm'):
        """Defines and downloads a waveform into the waveform memory.
        Returns useful waveform identifier."""

        # Adjust endianness for M9381/3A
        if 'M938' in self.instId:
            bigEndian = False
        else:
            bigEndian = True

        self.write('radio:arb:state off')
        self.write('modulation:state off')
        self.arbState = self.query('radio:arb:state?').strip()

        if wfmData.dtype != np.complex:
            raise TypeError('Invalid wfm type. IQ waveforms must be an array of complex values.')
        else:
            i = self.check_wfm(np.real(wfmData), bigEndian=bigEndian)
            q = self.check_wfm(np.imag(wfmData), bigEndian=bigEndian)

            wfm = self.iq_wfm_combiner(i, q)

        # M9381/3A Download Procedure
        if 'M938' in self.instId:
            try:
                self.write(f'memory:delete "{wfmID}"')
                self.query('*opc?')
                self.write(f'mmemory:delete "C:\\Temp\\{wfmID}"')
                self.query('*opc?')
                self.err_check()
            except error.SockInstError:
                # print('Waveform doesn\'t exist, skipping delete operation.')
                pass
            self.binblockwrite(f'mmemory:data "C:\\Temp\\{wfmID}",', wfm)
            self.write(f'memory:copy "C:\\Temp\\{wfmID}","{wfmID}"')
        # EXG/MXG/PSG Download Procedure
        else:
            self.binblockwrite(f'mmemory:data "WFM1:{wfmID}", ', wfm)
            self.write(f'radio:arb:waveform "WFM1:{wfmID}"')

        return wfmID

    @staticmethod
    def iq_wfm_combiner(i, q):
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

        repeats = wraparound_calc(len(wfm), self.gran, self.minLen)
        wfm = np.tile(wfm, repeats)
        rl = len(wfm)
        if rl < self.minLen:
            raise error.VSGError(f'Waveform length: {rl}, must be at least {self.minLen}.')
        if rl % self.gran != 0:
            raise error.GranularityError(f'Waveform must have a granularity of {self.gran}.')

        if bigEndian:
            return np.array(self.binMult * wfm, dtype=np.int16).byteswap()
        else:
            return np.array(self.binMult * wfm, dtype=np.int16)

    def delete_wfm(self, wfmID):
        """Stops output and deletes specified waveform."""
        self.stop()
        if 'M938' in self.instId:
            self.write(f'memory:delete "{wfmID}"')
        else:
            self.write(f'memory:delete "WFM1:{wfmID}"')
        self.err_check()

    def clear_all_wfm(self):
        """Stops output and deletes all iq waveforms."""
        self.stop()
        if 'M938' in self.instId:
            """UNTESTED PLEASE TEST"""
            self.write('memory:delete:all')
        else:
            self.write('mmemory:delete:wfm')
        self.err_check()

    def play(self, wfmID='wfm'):
        """Selects waveform and activates arb mode, RF output, and modulation."""
        if 'M938' in self.instId:
            self.write(f'radio:arb:waveform "{wfmID}"')
        else:
            self.write(f'radio:arb:waveform "WFM1:{wfmID}"')

        self.write('radio:arb:state on')
        self.arbState = self.query('radio:arb:state?').strip()
        self.write('output on')
        self.rfState = self.query('output?').strip()
        self.write('output:modulation on')
        self.modState = self.query('output:modulation?').strip()
        self.err_check()

    def stop(self):
        """Dectivates arb mode, RF output, and modulation."""
        self.write('radio:arb:state off')
        self.arbState = self.query('radio:arb:state?').strip()
        self.write('output off')
        self.rfState = self.query('output?').strip()
        self.write('output:modulation off')
        self.modState = self.query('output:modulation?').strip()


class AnalogUXG(communications.SocketInstrument):
    """Generic class for controlling the N5193A Analog UXG agile signal generators."""

    def __init__(self, host, port=5025, timeout=10, reset=False, clearMemory=False):
        super().__init__(host, port, timeout)
        if reset:
            self.write('*rst')
            self.query('*opc?')
        # Clear all files
        if clearMemory:
            self.clear_memory()
        self.host = host
        self.rfState = self.query('output?').strip()
        self.modState = self.query('output:modulation?').strip()
        self.streamState = self.query('stream:state?').strip()
        self.cf = float(self.query('frequency?').strip())
        self.amp = float(self.query('power?').strip())
        self.refSrc = self.query('roscillator:source?').strip()
        self.refFreq = 10e6
        self.mode = self.query('instrument?').strip()
        self.binMult = 32767

        # Set up separate socket for LAN PDW streaming
        self.lanStream = communications.socket.socket(
            communications.socket.AF_INET, communications.socket.SOCK_STREAM)
        self.lanStream.setblocking(False)
        self.lanStream.settimeout(timeout)
        # Can't connect until LAN streaming is turned on
        # self.lanStream.connect((host, 5033))

    def configure(self, rfState=0, modState=0, cf=1e9, amp=-130, mode='streaming'):
        """Sets the basic configuration for the UXG and populates class
        attributes accordingly. It should be called any time these
        settings are changed (ideally once directly after creating the
        UXG object)."""

        if not isinstance(cf, float) or cf <= 0:
            raise ValueError('Carrier frequency must be a positive floating point value.')
        if not isinstance(amp, int):
            raise ValueError('Amp argument must be an integer.')

        self.write(f'output {rfState}')
        self.rfState = self.query('output?').strip()
        self.write(f'output:modulation {modState}')
        self.modState = self.query('output:modulation?').strip()
        self.write(f'frequency {cf}')
        self.cf = float(self.query('frequency?').strip())
        self.write(f'power {amp}')
        self.amp = float(self.query('power?').strip())

        self.write(f'instrument {mode}')
        self.mode = self.query('instrument?').strip()

        if self.mode.lower() == 'str':
            # Stream state should be turned off until streaming is needed.
            self.write('stream:state off')
            self.streamState = self.query('stream:state?').strip()

        self.err_check()

    def sanity_check(self):
        """Prints out initialized values."""
        print('RF State:', self.rfState)
        print('Modulation State:', self.modState)
        print('Center Frequency:', self.cf)
        print('Output Amplitude:', self.amp)
        print('Reference source:', self.refSrc)
        print('Instrument mode:', self.mode)
        self.err_check()

    def open_lan_stream(self):
        """Open connection to port 5033 for LAN streaming to the UXG."""
        self.write('stream:state on')
        self.query('*opc?')
        self.lanStream.connect((self.host, 5033))

    def close_lan_stream(self):
        """Close LAN streaming port."""
        self.lanStream.shutdown(communications.socket.SHUT_RDWR)
        self.lanStream.close()

    @staticmethod
    def convert_to_floating_point(inputVal, exponentOffset, mantissaBits, exponentBits):
        """
        Description:    Computes modified floating point value represented
                        by specified floating point parameters
                        fp = gain * mantissa^mantissaExponent * 2^exponentOffset
        :param inputVal:
        :param exponentOffset:
        :param mantissaBits:
        :param exponentBits:
        :return floating point value corresponding to passed parameters:
        """

        # Error check largest number that can be represented in specified number of bits
        maxExponent = int((1 << exponentBits) - 1)
        maxMantissa = np.uint32(((1 << mantissaBits) - 1))

        exponent = int(math.floor(((math.log(inputVal) / math.log(2)) - exponentOffset)))
        # mantissa = 0

        if exponent > maxExponent:
            # Too big to represent
            exponent = maxExponent
            mantissa = maxMantissa
        elif exponent >= 0:
            mantissaScale = int((1 << mantissaBits))
            effectiveExponent = int(exponentOffset + exponent)
            # ldexp(X, Y) is the same as matlab pow2(X, Y) = > X * 2 ^ Y
            mantissa = np.uint32((((math.ldexp(inputVal, - effectiveExponent) - 1) * mantissaScale) + 0.5))
            if mantissa > maxMantissa:
                # Handle case where rounding causes the mantissa to overflow
                if exponent < maxExponent:
                    # Still representable
                    mantissa = 0
                    exponent += 1
                else:
                    # Handle slightly-too-big to represent case
                    mantissa = maxMantissa
        else:
            # Too small to represent
            mantissa = 0
            exponent = 0
        return ((np.uint32(exponent)) << mantissaBits) | mantissa

    @staticmethod
    def closest_m_2_n(inputVal, mantissaBits, exponent_bits):
        """
        Converts the specified value to the hardware representation in Mantissa*2^Exponent form
        Description:    Convert the specified value to the hardware
                        representation in Mantissa*2^Exponent form
        :param inputVal:
        :param mantissaBits:
        :param exponent_bits:
        :return:
        """

        success = True
        # exponent = 0
        # mantissa = 0
        maxMantissa = np.uint32((1 << mantissaBits) - 1)
        # inputVal <= mantissa max inputVal have exponent=0
        if inputVal < (maxMantissa + 0.5):
            exponent = 0
            mantissa = np.uint32((inputVal + 0.5))
            if mantissa > maxMantissa:
                mantissa = maxMantissa
        else:  # exponent > 0 (for value_ins that will have exponent>0 after rounding)
            # find exponent
            mantissaOut, possibleExponent = math.frexp(inputVal)
            possibleExponent -= mantissaBits
            # determine mantissa
            fracMantissa = float(inputVal / (1 << possibleExponent))
            # round to next N if that is closer
            if fracMantissa > (maxMantissa + 0.5 - 1e-9):
                mantissa = 1 << (mantissaBits - 1)
                possibleExponent += 1
            else:  # round mantissa to nearest
                mantissa = np.uint32((fracMantissa + 0.5))
                # do not exceed maximum mantissa
                if mantissa > maxMantissa:
                    mantissa = maxMantissa
            exponent = np.uint32(possibleExponent)

        return success, exponent, mantissa

    def chirp_closest_m_2_n(self, chirpRate, chirpRateRes=21.822):
        """
        Convert the specified value to the hardware representation in Mantissa*2^Exponent form for Chirp parameters
                Description:    Convert the specified value to the hardware
                                representation in Mantissa*2^Exponent form for Chirp
                                parameters
                :param chirpRate:
                :param chirpRateRes:
                :return:
        NOTE: I am not sure why the conversion factor of 21.82 needs to be there, but the math works out perfectly
        """

        output = np.uint32(0)
        mantissaBits = 13
        exponentBits = 4

        mantissaMask = np.uint32((1 << mantissaBits) - 1)
        # convert to clocks
        chirpValue = float(chirpRate) / float(chirpRateRes)
        success, exponent, mantissa = self.closest_m_2_n(chirpValue, mantissaBits, exponentBits)
        # compensate for exponent being multiplied by 2
        if exponent & 0x01:
            exponent += 1
            exponent >>= 1
            mantissa = np.uint32(mantissa / 2)
        else:
            exponent >>= 1
        if success:
            # print(exponent)
            # print(mantissaBits)
            # print(mantissa)
            # print(mantissaMask)
            output = np.uint32((exponent << mantissaBits) | (mantissa & mantissaMask))

        return output


    def bin_pdw_builder(self, operation=0, freq=1e9, phase=0, startTimeSec=0, width=0, power=0, markers=0,
                        pulseMode=0, phaseControl=0, bandAdjust=0, chirpControl=0, code=0,
                        chirpRate=0, freqMap=0):
        """This function builds a single format-1 PDW from a list of parameters.

        See User's Guide>Streaming Use>PDW Definitions section of
        Keysight UXG X-Series Agile Vector Adapter Online Documentation
        http://rfmw.em.keysight.com/wireless/helpfiles/n519xa-vector/n519xa-vector.htm"""

        pdwFormat = 1
        _freq = int(freq * 1024 + 0.5)
        if 180 < phase <= 360:
            phase -= 360
        _phase = int(phase * 4096 / 360 + 0.5)
        _startTimePs = int(startTimeSec * 1e12)
        _widthNs = int(width * 1e9)
        _power = self.convert_to_floating_point(math.pow(10, power / 20), -26, 10, 5)
        _chirpRate = self.chirp_closest_m_2_n(chirpRate)

        # Build PDW
        pdw = np.zeros(7, dtype=np.uint32)
        # Word 0: Mask pdw format (3 bits), operation (2 bits), and the lower 27 bits of freq
        pdw[0] = (pdwFormat | operation << 3 | _freq << 5) & 0xFFFFFFFF
        # Word 1: Mask the upper 20 bits (47 - 27) of freq and phase (12 bits)
        pdw[1] = (_freq >> 27 | _phase << 20) & 0xFFFFFFFF
        # Word 2: Lower 32 bits of startTimePs
        pdw[2] = _startTimePs & 0xFFFFFFFF
        # Word 3: Upper 32 bits of startTimePS
        pdw[3] = (_startTimePs & 0xFFFFFFFF00000000) >> 32
        # Word 4: Pulse Width (32 bits)
        pdw[4] = _widthNs
        # Word 5: Mask power (15 bits), markers (12 bits), pulseMode (2 bits), phaseControl (1 bit), and bandAdjust (2 bits)
        pdw[5] = _power | markers << 15 | pulseMode << 27 | phaseControl << 29 | bandAdjust << 30
        # Word 6: Mask wIndex (16 bits), 12 reserved bits, and wfmMkrMask (4 bits)
        pdw[6] = chirpControl | code << 3 | _chirpRate << 12 | freqMap << 29

        return pdw

    # noinspection PyRedundantParentheses
    def bin_pdw_file_builder(self, pdwList):
        """Builds a binary PDW file with a padding block to ensure the
        PDW section begins at an offset of 4096 bytes (required by UXG).

        pdwList is a list of lists. Each inner list contains a single
        pulse descriptor word.

        See User's Guide>Streaming Use>PDW File Format section of
        Keysight UXG X-Series Agile Vector Adapter Online Documentation
        http://rfmw.em.keysight.com/wireless/helpfiles/n519xa-vector/n519xa-vector.htm"""

        # Header section, all fixed values
        fileId = b'STRM'
        version = (1).to_bytes(4, byteorder='little')
        # No reason to have > one 4096 byte offset to PDW data.
        offset = ((1 << 1) & 0x3fffff).to_bytes(4, byteorder='little')
        magic = b'KEYS'
        res0 = (0).to_bytes(16, byteorder='little')
        flags = (0).to_bytes(4, byteorder='little')
        uniqueId = (0).to_bytes(4, byteorder='little')
        dataId = (16).to_bytes(4, byteorder='little')
        res1 = (0).to_bytes(4, byteorder='little')
        header = [fileId, version, offset, magic, res0, flags, uniqueId, dataId, res1]

        # Padding block, all fixed values
        padBlockId = (1).to_bytes(4, byteorder='little')
        res3 = (0).to_bytes(4, byteorder='little')
        size = (4016).to_bytes(8, byteorder='little')
        # 4016 bytes of padding ensures that the first PDw begins @ byte 4097
        padData = (0).to_bytes(4016, byteorder='little')
        padding = [padBlockId, res3, size, padData]

        # PDW block
        pdwBlockId = (16).to_bytes(4, byteorder='little')
        res4 = (0).to_bytes(4, byteorder='little')
        pdwSize = (0xffffffffffffffff).to_bytes(8, byteorder='little')
        pdwBlock = [pdwBlockId, res4, pdwSize]

        # Build PDW file from header, padBlock, pdwBlock, and PDWs
        pdwFile = header + padding + pdwBlock
        pdwFile += [self.bin_pdw_builder(*p) for p in pdwList]
        pdwFile += [(0).to_bytes(24, byteorder='little')]
        # Convert arrays of data to a single byte-type variable
        pdwFile = b''.join(pdwFile)

        self.err_check()

        return pdwFile

    def download_bin_pdw_file(self, pdwFile, pdwName='wfm'):
        """Downloads binary PDW file to PDW directory in UXG."""
        self.binblockwrite(f'memory:data "/USER/PDW/{pdwName}",', pdwFile)
        self.err_check()

    def stream_play(self, pdwID='pdw'):
        """Assigns pdw/windex, activates RF output, modulation, and
        streaming mode, and triggers streaming output."""

        self.write('stream:source file')
        self.write(f'stream:source:file:name "{pdwID}"')
        self.err_check()

        # Turn on output, activate streaming, and send trigger command.
        self.write('output on')
        self.rfState = self.query('output?').strip()
        self.err_check()
        self.write('output:modulation on')
        self.modState = self.query('output:modulation?').strip()
        self.write('source:stream:state on')
        self.err_check()
        self.streamState = self.query('stream:state?').strip()
        self.err_check()
        self.write('stream:trigger:play:immediate')

    def stream_stop(self):
        """Deactivates RF output, modulation, and streaming mode."""
        self.write('output off')
        self.rfState = self.query('output?').strip()
        self.write('output:modulation off')
        self.modState = self.query('output:modulation?').strip()
        self.write('stream:state off')
        self.streamState = self.query('stream:state?').strip()
        self.err_check()


class VectorUXG(communications.SocketInstrument):
    """Generic class for controlling the N5194A + N5193A (Vector + Analog)
    UXG agile signal generators."""

    def __init__(self, host, port=5025, timeout=10, reset=False, clearMemory=False):
        super().__init__(host, port, timeout)
        if reset:
            self.write('*rst')
            self.query('*opc?')
        # Clear all waveform, pdw, and windex files
        if clearMemory:
            self.clear_memory()
        self.host = host
        self.rfState = self.query('output?').strip()
        self.modState = self.query('output:modulation?').strip()
        self.arbState = self.query('radio:arb:state?').strip()
        self.streamState = self.query('stream:state?').strip()
        self.cf = float(self.query('frequency?').strip())
        self.amp = float(self.query('power?').strip())
        self.iqScale = float(self.query('radio:arb:rscaling?').strip())
        self.refSrc = self.query('roscillator:source?').strip()
        self.refFreq = 10e6
        self.mode = self.query('instrument:select?').strip()
        self.fs = float(self.query('radio:arb:sclock:rate?').strip())
        self.gran = int(self.query('radio:arb:information:quantum?').strip())
        self.minLen = int(self.query('radio:arb:information:slength:minimum?').strip())
        self.binMult = 32767

        # Set up separate socket for LAN PDW streaming
        self.lanStream = communications.socket.socket(
            communications.socket.AF_INET, communications.socket.SOCK_STREAM)
        self.lanStream.setblocking(False)
        self.lanStream.settimeout(timeout)
        # Can't connect until LAN streaming is turned on
        # self.lanStream.connect((host, 5033))

    def configure(self, rfState=0, modState=0, cf=1e9, amp=-120, iqScale=70):
        """Sets the basic configuration for the UXG and populates class
        attributes accordingly. It should be called any time these
        settings are changed (ideally once directly after creating the
        UXG object)."""

        if not isinstance(cf, float) or cf <= 0:
            raise ValueError('Carrier frequency must be a positive floating point value.')
        if not isinstance(amp, int):
            raise ValueError('Amp argument must be an integer.')
        if not isinstance(iqScale, int) or iqScale <= 0 or iqScale > 100:
            raise ValueError('iqScale argument must be an integer between 1 and 100.')

        self.write(f'output {rfState}')
        self.rfState = self.query('output?').strip()
        self.write(f'output:modulation {modState}')
        self.modState = self.query('output:modulation?').strip()
        self.write(f'frequency {cf}')
        self.cf = float(self.query('frequency?').strip())
        self.write(f'power {amp}')
        self.amp = float(self.query('power?').strip())
        self.write(f'radio:arb:rscaling {iqScale}')
        self.iqScale = float(self.query('radio:arb:rscaling?').strip())

        # Arb state can only be turned on after a waveform has been loaded/selected.
        self.write('radio:arb:state off')
        self.arbState = self.query('radio:arb:state?').strip()

        # Stream state should be turned off until streaming is needed.
        self.write('stream:state off')
        self.streamState = self.query('stream:state?').strip()

        self.err_check()

    def sanity_check(self):
        """Prints out initialized values."""
        print('RF State:', self.rfState)
        print('Modulation State:', self.modState)
        print('Center Frequency:', self.cf)
        print('Output Amplitude:', self.amp)
        print('Reference source:', self.refSrc)
        print('Internal Arb Sample Rate:', self.fs)
        print('IQ Scaling:', self.iqScale)
        self.err_check()

    def clear_memory(self):
        """Clears all waveform, pdw, and windex files. This function
        MUST be called prior to downloading waveforms and making
        changes to an existing pdw file."""

        self.write('stream:state off')
        self.write('radio:arb:state off')
        self.write('memory:delete:binary')
        self.write('mmemory:delete:wfm')
        self.query('*opc?')
        self.err_check()

    def open_lan_stream(self):
        """Open connection to port 5033 for LAN streaming to the UXG."""
        self.write('stream:state on')
        self.query('*opc?')
        self.lanStream.connect((self.host, 5033))

    def close_lan_stream(self):
        """Close LAN streaming port."""
        self.lanStream.shutdown(communications.socket.SHUT_RDWR)
        self.lanStream.close()

    @staticmethod
    def bin_pdw_builder(operation=0, freq=1e9, phase=0, startTimeSec=0, power=0, markers=0,
                        phaseControl=0, rfOff=0, wIndex=0, wfmMkrMask=0):
        """This function builds a single format-1 PDW from a list of parameters.

        See User's Guide>Streaming Use>PDW Definitions section of
        Keysight UXG X-Series Agile Vector Adapter Online Documentation
        http://rfmw.em.keysight.com/wireless/helpfiles/n519xa-vector/n519xa-vector.htm"""

        pdwFormat = 1
        _freq = int(freq * 1024 + 0.5)
        _phase = int(phase * 4096 / 360 + 0.5)
        _startTimePs = int(startTimeSec * 1e12)
        _power = int((power + 140) / 0.005 + 0.5)

        # Build PDW
        pdw = np.zeros(6, dtype=np.uint32)
        # Word 0: Mask pdw format (3 bits), operation (2 bits), and the lower 27 bits of freq
        pdw[0] = (pdwFormat | operation << 3 | _freq << 5) & 0xFFFFFFFF
        # Word 1: Mask the upper 20 bits (47 - 27) of freq and phase (12 bits)
        pdw[1] = (_freq >> 27 | _phase << 20) & 0xFFFFFFFF
        # Word 2: Lower 32 bits of startTimePs
        pdw[2] = _startTimePs & 0xFFFFFFFF
        # Word 3: Upper 32 bits of startTimePS
        pdw[3] = (_startTimePs & 0xFFFFFFFF00000000) >> 32
        # Word 4: Mask power (15 bits), markers (12 bits), phaseControl (1 bit), and rfOff (1 bit)
        pdw[4] = _power | markers << 15 | phaseControl << 27 | rfOff << 28
        # Word 5: Mask wIndex (16 bits), 12 reserved bits, and wfmMkrMask (4 bits)
        pdw[5] = wIndex | 0b000000000000 << 16 | wfmMkrMask << 28

        return pdw

    # noinspection PyRedundantParentheses
    def bin_pdw_file_builder(self, pdwList):
        """Builds a binary PDW file with a padding block to ensure the
        PDW section begins at an offset of 4096 bytes (required by UXG).

        pdwList is a list of lists. Each inner list contains a single
        pulse descriptor word.

        See User's Guide>Streaming Use>PDW File Format section of
        Keysight UXG X-Series Agile Vector Adapter Online Documentation
        http://rfmw.em.keysight.com/wireless/helpfiles/n519xa-vector/n519xa-vector.htm"""

        # Header section, all fixed values
        fileId = b'STRM'
        version = (1).to_bytes(4, byteorder='little')
        # No reason to have > one 4096 byte offset to PDW data.
        offset = ((1 << 1) & 0x3fffff).to_bytes(4, byteorder='little')
        magic = b'KEYS'
        res0 = (0).to_bytes(16, byteorder='little')
        flags = (0).to_bytes(4, byteorder='little')
        uniqueId = (0).to_bytes(4, byteorder='little')
        dataId = (64).to_bytes(4, byteorder='little')
        res1 = (0).to_bytes(4, byteorder='little')
        header = [fileId, version, offset, magic, res0, flags, uniqueId, dataId, res1]

        # Padding block, all fixed values
        padBlockId = (1).to_bytes(4, byteorder='little')
        res3 = (0).to_bytes(4, byteorder='little')
        size = (4016).to_bytes(8, byteorder='little')
        # 4016 bytes of padding ensures that the first PDw begins @ byte 4097
        padData = (0).to_bytes(4016, byteorder='little')
        padding = [padBlockId, res3, size, padData]

        # PDW block
        pdwBlockId = (16).to_bytes(4, byteorder='little')
        res4 = (0).to_bytes(4, byteorder='little')
        pdwSize = (0xffffffffffffffff).to_bytes(8, byteorder='little')
        pdwBlock = [pdwBlockId, res4, pdwSize]

        # Build PDW file from header, padBlock, pdwBlock, and PDWs
        pdwFile = header + padding + pdwBlock
        pdwFile += [self.bin_pdw_builder(*p) for p in pdwList]
        # Convert arrays of data to a single byte-type variable
        pdwFile = b''.join(pdwFile)

        self.err_check()

        return pdwFile

    def csv_pdw_file_download(self, fileName, fields=('Operation', 'Time'),
                              data=((1, 0), (2, 100e-6))):
        """Builds a CSV PDW file, sends it into the UXG, and converts it to a binary PDW file."""
        # Write header fields separated by commas and terminated with \n
        pdwCsv = ','.join(fields) + '\n'
        for row in data:
            # Write subsequent rows with data values separated by commas and terminated with \n
            # The .join() function requires a list of strings, so convert numbers in row to strings
            rowString = ','.join([f'{r}' for r in row]) + '\n'
            pdwCsv += rowString

        # Delete pdw csv file if already exists, continue script if it doesn't
        try:
            self.write('stream:state off')
            self.write(f'memory:delete "{fileName}.csv"')
            self.err_check()
        except error.SockInstError:
            pass
        self.binblockwrite(f'memory:data "{fileName}.csv", ', pdwCsv.encode('utf-8'))

        """Note: memory:import:stream imports/converts csv to pdw AND
        assigns the resulting pdw and waveform index files as the stream
        source. There is no need to send the stream:source:file or 
        stream:source:file:name commands because they are sent
        implicitly by memory:import:stream."""

        self.write(f'memory:import:stream "{fileName}.csv", "{fileName}"')
        self.query('*opc?')
        self.err_check()

    def csv_windex_file_download(self, windex):
        """Write header fields separated by commas and terminated with \n

        windex is a dictionary:
        {'fileName': '<fileName>', 'wfmNames': ['name0', 'name1',... 'nameN']}"""

        windexCsv = 'Id,Filename\n'
        for i in range(len(windex['wfmNames'])):
            windexCsv += f'{i},{windex["wfmNames"][i]}\n'

        self.binblockwrite(f'memory:data "{windex["fileName"]}.csv", ', windexCsv.encode('utf-8'))

        """Note: memory:import:windex imports/converts csv to waveform
        index file AND assigns the resulting file as the waveform index
        manager. There is no need to send the stream:windex:select 
        command because it is sent implicitly by memory:import:windex."""
        self.write(f'memory:import:windex "{windex["fileName"]}.csv", "{windex["fileName"]}"')
        self.query('*opc?')
        self.err_check()

    def download_wfm(self, wfmData, wfmID='wfm'):
        """Defines and downloads a waveform into the waveform memory.
        Returns useful waveform identifier."""

        if wfmData.dtype != np.complex:
            raise TypeError('Invalid wfm type. IQ waveforms must be an array of complex values.')
        else:
            i = self.check_wfm(np.real(wfmData))
            q = self.check_wfm(np.imag(wfmData))

            wfm = self.iq_wfm_combiner(i, q)
        self.write('radio:arb:state off')

        self.arbState = self.query('radio:arb:state?').strip()
        self.binblockwrite(f'memory:data "WFM1:{wfmID}", ', wfm)

        return wfmID

    @staticmethod
    def iq_wfm_combiner(i, q):
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

        repeats = wraparound_calc(len(wfm), self.gran, self.minLen)
        wfm = np.tile(wfm, repeats)
        rl = len(wfm)

        if rl < self.minLen:
            raise error.VSGError(f'Waveform length: {rl}, must be at least {self.minLen}.')
        if rl % self.gran != 0:
            raise error.GranularityError(f'Waveform must have a granularity of {self.gran}.')

        if bigEndian:
            return np.array(self.binMult * wfm, dtype=np.uint16).byteswap()
        else:
            return np.array(self.binMult * wfm, dtype=np.uint16)

    def arb_play(self, wfmID='wfm'):
        """Selects waveform and activates RF output, modulation, and arb mode."""
        self.write(f'radio:arb:waveform "WFM1:{wfmID}"')
        self.write('radio:arb:state on')
        self.arbState = self.query('radio:arb:state?').strip()
        self.write('output on')
        self.rfState = self.query('output?').strip()
        self.write('output:modulation on')
        self.modState = self.query('output:modulation?').strip()
        self.err_check()

    def arb_stop(self):
        """Dectivates RF output, modulation, and arb mode."""
        self.write('output off')
        self.rfState = self.query('output?').strip()
        self.write('output:modulation off')
        self.modState = self.query('output:modulation?').strip()
        self.write('radio:arb:state off')
        self.arbState = self.query('radio:arb:state?').strip()
        self.err_check()

    def stream_play(self, pdwID='pdw', wIndexID=None):
        """Assigns pdw/windex, activates RF output, modulation, and
        streaming mode, and triggers streaming output."""

        self.write('stream:source file')
        self.write(f'stream:source:file:name "{pdwID}"')

        # If wIndexID is unspecified, use the same name as the pdw file.
        if wIndexID is None:
            self.write(f'stream:windex:select "{pdwID}"')
        else:
            self.write(f'stream:windex:select "{wIndexID}"')

        # Turn on output, activate streaming, and send trigger command.
        self.write('output on')
        self.rfState = self.query('output?').strip()
        self.write('output:modulation on')
        self.modState = self.query('output:modulation?').strip()
        self.write('stream:state on')
        self.streamState = self.query('stream:state?').strip()
        self.write('stream:trigger:play:immediate')
        self.err_check()

    def stream_stop(self):
        """Deactivates RF output, modulation, and streaming mode."""
        self.write('output off')
        self.rfState = self.query('output?').strip()
        self.write('output:modulation off')
        self.modState = self.query('output:modulation?').strip()
        self.write('stream:state off')
        self.streamState = self.query('stream:state?').strip()
        self.err_check()
