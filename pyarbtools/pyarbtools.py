"""
pyarbtools 0.1.0
Author: Morgan Allison, Keysight RF/uW Application Engineer
Updated: 10/18
Builds instrument specific classes for each AWG. The classes include minimum
waveform length/granularity checks, binary waveform formatting, sequencer
length/granularity checks, sample rate checks, etc. per AWG.
Uses socket_instrument.py for instrument communication.
Python 3.6.4
Tested on M8190A, M8195A, N5194A, N5182B, E8257D
"""

from socket_instrument import *
from scipy.io import loadmat
import wfmBuilder


class AWGError(Exception):
    """AWG Exception class"""


class VSGError(Exception):
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
            raise AWGError(f'Waveform length: {rl}, must be at least {self.minLen}.')
        if rl % self.gran != 0:
            raise AWGError(f'Waveform must have a granularity of {self.gran}.')

        return np.array(self.binMult * wfm, dtype=np.int16) << self.binShift

    def configure(self, res='wsp', clkSrc='int', fs=7.2e9, refSrc='axi', refFreq=100e6, out1='dac', out2='dac', func1='arb', func2='arb', cf1=2e9, cf2=2e9):
        """Sets basic configuration for M8190A and populates class attributes accordingly."""
        self.set_resolution(res)

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

    @staticmethod
    def iq_wfm_combiner(i, q):
        """Combines i and q wfms into a single interleaved wfm for download to AWG."""
        iq = np.empty(2 * len(i), dtype=np.int16)
        iq[0::2] = i
        iq[1::2] = q
        return iq

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
            if self.intFactor == 3:
                self.idleGran = 8
            elif self.intFactor == 12:
                self.idleGran = 2
            elif self.intFactor == 24 or self.intFactor == 48:
                self.idleGran = 1
        else:
            raise AWGError('Invalid resolution selected.')

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
            raise AWGError(f'Waveform length: {rl}, must be at least {self.minLen}.')
        if rl % self.gran != 0:
            raise AWGError(f'Waveform must have a granularity of {self.gran}.')

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
            self.query('*opc?')
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
            raise VSGError('Unknown refSrc selected.')
        self.gran = 2
        self.minLen = 60
        self.binMult = 32767

    def configure(self, rfState=0, modState=0, cf=1e9, amp=-130, iqScale=70, refSrc='int', fs=200e6):
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
            raise VSGError('Unknown refSrc selected.')
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
        print('Reference Source:', self.refSrc)
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

        rl = len(wfm)
        if rl < self.minLen:
            raise VSGError(f'Waveform length: {rl}, must be at least {self.minLen}.')
        if rl % self.gran != 0:
            # vsg.query('*opc?')
            raise VSGError(f'Waveform must have a granularity of {self.gran}.')

        if bigEndian:
            return np.array(self.binMult * wfm, dtype=np.int16).byteswap()
        else:
            return np.array(self.binMult * wfm, dtype=np.int16)


class UXG(SocketInstrument):
    """Generic class for controlling the N5194A + N5193A (Vector + Analog)
    UXG agile signal generators."""

    def __init__(self, host, port=5025, timeout=5, reset=False):
        super().__init__(host, port, timeout)
        print(self.instId)
        if reset:
            self.write('*rst')
            self.query('*opc?')
        self.host = host
        self.rfState = self.query('output?').strip()
        self.modState = self.query('output:modulation?').strip()
        self.cf = float(self.query('frequency?').strip())
        self.amp = float(self.query('power?').strip())
        self.mode = self.query('instrument:select?').strip()
        self.fs = float(self.query('radio:arb:sclock:rate?').strip())
        self.gran = int(self.query('radio:arb:information:quantum?').strip())
        self.minLen = int(self.query('radio:arb:information:slength:minimum?').strip())
        self.binMult = 32767

        # Set up separate socket for LAN PDW streaming
        self.lanStream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lanStream.setblocking(False)
        self.lanStream.settimeout(timeout)
        # Can't connect until LAN streaming is turned on
        # self.lanStream.connect((host, 5033))

    def configure(self, rfState=0, modState=0, cf=1e9, amp=-130, iqScale=70, refSrc='int', fs=200e6):
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
            raise VSGError('Unknown refSrc selected.')
        self.write(f'radio:arb:sclock:rate {fs}')
        self.fs = float(self.query('radio:arb:sclock:rate?').strip())
        self.write(f'radio:arb:rscaling {iqScale}')
        self.iqScale = float(self.query('radio:arb:rscaling?').strip())

        self.err_check()

    def open_lan_stream(self):
        """Open connection to port 5033 for LAN streaming to the UXG."""
        self.lanStream.connect((self.host, 5033))

    def close_lan_stream(self):
        """Close LAN streaming port."""
        self.lanStream.shutdown(socket.SHUT_RDWR)
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
        # Word 0: Mask pdw format (3 bits), operation (2 bits), and the lower 27 bits (32 - 5) of freq
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

        with open('C:\\Users\\moalliso\\Desktop\\pdwtest', 'wb') as f:
            f.write(pdwFile)

        return pdwFile

    def csv_pdw_file_download(self, fileName, fields=('Operation', 'Time'), data=((1, 0), (2, 100e-6))):
        """Builds a CSV PDW file, sends it into the UXG, and converts it to a binary PDW file."""

        # Write header fields separated by commas and terminated with \n
        pdwCsv = ','.join(fields) + '\n'
        for row in data:
            # Write subsequent rows with data values separated by commas and terminated with \n
            # The .join() function requires a list of strings, so convert numbers in row to strings
            rowString = ','.join([f'{r}' for r in row]) + '\n'
            pdwCsv += rowString

        self.write(f'memory:delete "{fileName}.csv"')
        self.binblockwrite(f'memory:data "{fileName}.csv", ', pdwCsv.encode('utf-8'))

        """Note: memory:import:stream imports/converts csv to pdw AND
        assigns the resulting pdw and waveform index files as the stream
        source. There is no need to send the stream:source:file or 
        stream:source:file:name commands because they are sent
        implicitly by memory:import:stream."""

        self.write(f'memory:import:stream "{fileName}.csv", "{fileName}"')
        self.query('*opc?')

    def csv_windex_file_download(self, windex):
        """Write header fields separated by commas and terminated with \n

        windex is a dictionary:
        {'fileName': '<fileName>', 'wfmNames': ['name0', 'name1',... 'nameN']}"""

        windexCsv = 'Id,Filename\n'
        for i in range(len(windex['wfmNames'])):
            windexCsv += f'{i},{windex["wfmNames"][i]}\n'

        self.write(f'memory:delete "{windex["fileName"]}.csv"')
        self.binblockwrite(f'memory:data "{windex["fileName"]}.csv", ', windexCsv.encode('utf-8'))

        """Note: memory:import:windex imports/converts csv to waveform
        index file AND assigns the resulting file as the waveform index
        manager. There is no need to send the stream:windex:select 
        command because it is sent implicitly by memory:import:windex."""
        self.write(f'memory:import:windex "{windex["fileName"]}.csv", "{windex["fileName"]}"')
        self.query('*opc?')

    def download_matlab_wfm(self, fileName, zeroLast=False):
        """Imports a .mat file built in iqtools and formats it
        appropriately for transfer to UXG."""

        # Extract the file name from the full path and remove .mat extension
        name = fileName.split('\\')[-1].replace('.mat', '')

        # Load the iqdata member of the .mat structure
        iq = loadmat(fileName)['iqdata']

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

        rl = len(wfm)
        if rl < self.minLen:
            raise VSGError(f'Waveform length: {rl}, must be at least {self.minLen}.')
        if rl % self.gran != 0:
            raise VSGError(f'Waveform must have a granularity of {self.gran}.')

        if bigEndian:
            return np.array(self.binMult * wfm, dtype=np.uint16).byteswap()
        else:
            return np.array(self.binMult * wfm, dtype=np.uint16)
