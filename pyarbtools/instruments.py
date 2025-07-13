"""
instruments
Author: Morgan Allison, Keysight RF/uW Application Engineer
Builds instrument specific classes for each signal generator.
The classes include minimum waveform length/granularity checks, binary
waveform formatting, sequencer length/granularity checks, sample rate
checks, etc. per instrument.
Tested on M8190A, M8195A, M8196A, N5182B, E8257D, M9383A, N5193A, N5194A
"""

import numpy as np
import socketscpi
import pyvisa

from pyarbtools import error

"""
TODO:
* Add a function for IQ adjustments in VSG class
* Add multithreading for waveform download and wfmBuilder
* Add a multi-binblockwrite feature for download_wfm in the case of
    waveform size > 1 GB
"""


def wraparound_calc(length, gran, minLen):
    """
    HELPER FUNCTION
    Computes the number of times to repeat a waveform based on
    generator granularity requirements.
    Args:
        length (int): Length of waveform
        gran (int): Granularity of waveform, determined by signal generator class
        minLen: Minimum wfm length, determined by signal generator class

    Returns:
        (int) Number of repeats required to satisfy gran and minLen requirements
    """

    repeats = 1
    temp = length
    while temp % gran != 0 or temp < minLen:
        temp += length
        repeats += 1
    if repeats > 1:
        print(f"Information: Waveform repeated {repeats} times.")
    return repeats


class SignalGeneratorBase:
    def __init__(self, ipAddress, apiType="socketscpi", timeout=10, **kwargs):
            """
            Args:
            ipAddress (string): Instrument host IP address. Argument is a string containing a valid IP address.
            apiType (string): Chooses whether to use PyVISA or socketscpi ["pyvisa", "socketscpi"].
            timeout (int): Timeout in seconds.
            
            Keyword Args:
            protocol (string): LAN protocol used to communicate with the instrument ("vxi11", "hislip", "socket"). Note this is only usable with PyVISA.
            port (int): Port used by the instrument to facilitate communication (socket default is 5025, vxi11 and hislip defaults are 0).
            """

            self.apiType = apiType

            for key, value in kwargs.items():
                if key == "protocol":
                    protocol = value
                elif key == "port":
                    port = value
                # No good reason to use delay behavior in an instrument control scenario
                # elif key == "noDelay":
                    # noDelay = value
                else:
                    raise KeyError(f'{key} is not a valid keyword argument.')

            if self.apiType == "socketscpi":
                try:
                    self.instance = socketscpi.SocketInstrument(ipAddress, port=port, timeout=timeout, noDelay=True)
                except NameError:
                    self.instance = socketscpi.SocketInstrument(ipAddress, port=5025, timeout=timeout, noDelay=True)
            elif self.apiType == "pyvisa":
                if protocol.lower() == "vxi11":
                    self.instance = pyvisa.ResourceManager().open_resource(f"tcpip::{ipAddress}::inst{port}::instr")
                elif protocol.lower() == "hislip":
                    self.instance = pyvisa.ResourceManager().open_resource(f"tcpip::{ipAddress}::hislip{port}::instr")
                elif protocol.lower() == "socket":
                    raise error.InstrumentError(f'socket protocol in PyVISA is not currently working, use "hislip" or "vxi11"')
                    # self.instance = pyvisa.ResourceManager().open_resource(f"tcpip0::{ipAddress}::{port}::socket")
                else:
                    raise ValueError('Invalid protocol selection. Use "vxi11", "hislip", or "socket".')
                # PyVISA's open_resource() method doesn't have a timeout argument, so use a separate method to set it.
                self.instance.timeout = timeout * 1000
            else:
                raise ValueError(f'"{self.apiType}" is not a valid apiType, use "socketscpi" or "pyvisa".')
            
            self.instId = self.instance.query("*idn?")

    def __getattr__(self, __name: str):
        """This is a passthrough method that allows the base class to access attributes from the parent class.
        See the accepted answer at
        https://stackoverflow.com/questions/65754399/conditional-inheritance-based-on-arguments-in-python"""
        return self.instance.__getattribute__(__name)
        
    def err_check(self):
        """Prints out all errors and clears error queue. Raises InstrumentError with the info of the error encountered."""

        err = []
        cmd = 'SYST:ERR?'

        # Strip out extra characters
        temp = self.query(cmd)
        temp = temp.strip().replace('+', '').replace('-', '')
        # Read all errors until none are left
        while temp != '0,"No error"':
            # Build list of errors
            print(temp)
            err.append(temp)
            temp = self.query(cmd)
            temp = temp.strip().replace('+', '').replace('-', '')
        if err:
            raise error.InstrumentError(err)

class M8190A(SignalGeneratorBase):
    """Generic class for controlling a Keysight M8190A AWG.

    Attributes:
        res (str): DAC resolution. Possible values are 'wsp', 'wpr', 'intx3', 'intx12', 'intx24', and 'intx48'
        clkSrc (str): Sample clock source
        fs (float): Sample clock rate
        refSrc (str): Reference clock source
        refFreq (float): Reference clock frequency
        out1 (str): Output path for channel 1
        out2 (str): Output path for channel 2
        amp1 (float): Output amplitude for channel 1
        amp2 (float): Output amplitude for channel 2
        func1 (str): AWG function for channel 1
        func2 (str): AWG function for channel 2
        cf1 (float): Carrier frequency for channel 1
        cf2 (float): Carrier frequency for channel 2

    TODO
        Add check to ensure that the correct instrument is connected
    """

    def __init__(self, ipAddress, apiType="socketscpi", timeout=10, reset=False, **kwargs):
        super().__init__(ipAddress, apiType=apiType, timeout=timeout, **kwargs)
        if reset:
            self.write("*rst")
            self.query("*opc?")
            self.write("abort")
        
        # Query all settings from AWG and store them as class attributes
        self.res = self.query("trace1:dwidth?").strip().lower()
        self.func1 = self.query("func1:mode?").strip()
        self.func2 = self.query("func2:mode?").strip()
        self.clkSrc = self.query("frequency:raster:source?").strip().lower()
        self.fs = float(self.query("frequency:raster?").strip())
        self.bbfs = self.fs
        self.refSrc = self.query("roscillator:source?").strip()
        self.refFreq = float(self.query("roscillator:frequency?").strip())
        self.out1 = self.query("output1:route?").strip()
        self.out2 = self.query("output2:route?").strip()
        self.func1 = self.query("func1:mode?").strip()
        self.func2 = self.query("func2:mode?").strip()
        self.cf1 = float(self.query("carrier1:freq?").strip().split(",")[0])
        self.cf2 = float(self.query("carrier2:freq?").strip().split(",")[0])
        self.amp1 = self.query(f"{self.out1}1:voltage:amplitude?")
        self.amp2 = self.query(f"{self.out2}1:voltage:amplitude?")

        # Initialize waveform format constants and populate them with check_resolution()
        self.gran = 0
        self.minLen = 0
        self.binMult = 0
        self.binShift = 0
        self.intFactor = 1
        self.idleGran = 0
        self.check_resolution()

    def sanity_check(self):
        """Prints out user-accessible class attributes."""

        print("Sample rate:", self.fs)
        print("Baseband Sample Rate:", self.bbfs)
        print("Resolution:", self.res)
        print(f"Output path 1: {self.out1}, Output path 2: {self.out2}")
        print(f"Carrier 1: {self.cf1} Hz, Carrier 2: {self.cf2}")
        print(f"Function 1: {self.func1}, Function 2: {self.func2}")
        print("Ref source:", self.refSrc)
        print("Ref frequency:", self.refFreq)

    # def configure(self, res='wsp', clkSrc='int', fs=7.2e9, refSrc='axi', refFreq=100e6, out1='dac',
    #               out2='dac', amp1=0.65, amp2=0.65, func1='arb', func2='arb', cf1=1e9, cf2=1e9):
    def configure(self, **kwargs):
        """
        Sets basic configuration for M8190A and updates class attributes accordingly.
        Keyword Arguments:
            res (str): DAC resolution
            clkSrc (str): Sample clock source
            fs (float): Sample clock rate
            refSrc (str): Reference clock source
            refFreq (float): Reference clock frequency
            out1 (str): Output path for channel 1
            out2 (str): Output path for channel 2
            amp1 (float): Output amplitude for channel 1
            amp2 (float): Output amplitude for channel 2
            func1 (str): AWG function for channel 1
            func2 (str): AWG function for channel 2
            cf1 (float): Carrier frequency for channel 1
            cf2 (float): Carrier frequency for channel 2
        """

        # Stop output before doing anything else
        self.write("abort")

        # Check to see which keyword arguments the user sent and call the appropriate function
        for key, value in kwargs.items():
            if key == "res":
                self.set_resolution(value)
            elif key == "clkSrc":
                self.set_clkSrc(value)
            elif key == "fs":
                self.set_fs(value)
            elif key == "refSrc":
                self.set_refSrc(value)
            elif key == "refFreq":
                self.set_refFreq(value)
            elif key == "out1":
                self.set_output(1, value)
            elif key == "out2":
                self.set_output(2, value)
            elif key == "amp1":
                self.set_amp(1, value)
            elif key == "amp2":
                self.set_amp(2, value)
            elif key == "func1":
                self.set_func(1, value)
            elif key == "func2":
                self.set_func(2, value)
            elif key == "cf1":
                self.set_cf(1, value)
            elif key == "cf2":
                self.set_cf(2, value)
            else:
                raise KeyError(f'Invalid keyword argument: "{key}"')
        self.err_check()

    def set_clkSrc(self, clkSrc):
        """
        Sets and reads clock source parameter using SCPI commands.
        Args:
            clkSrc (str): Sample clock source ('int', 'ext')
        """

        if clkSrc.lower() not in ["int", "ext"]:
            raise ValueError("'clkSrc' argument must be 'int' or 'ext'.")
        self.write(f"frequency:raster:source {clkSrc}")
        self.clkSrc = self.query("frequency:raster:source?").strip().lower()

    def set_fs(self, fs):
        """
        Sets and reads sample clock rate using SCPI commands.
        Args:
            fs (float): Sample clock rate.
        """

        if not isinstance(fs, (int, float)) or fs <= 0:
            raise ValueError("Sample rate must be a positive floating point value.")

        if "int" in self.clkSrc:
            self.write(f"frequency:raster {fs}")
            self.fs = float(self.query("frequency:raster?").strip())
        else:
            self.write(f"frequency:raster:external {fs}")
            self.fs = float(self.query("frequency:raster:external?").strip())

        self.bbfs = self.fs / self.intFactor

    def set_output(self, ch, out):
        """
        Sets and reads output signal path for a given channel using SCPI commands.
        Args:
            ch (int): Channel to be configured
            out (str): Output path for channel ('dac', 'dc', 'ac')
        """

        if out.lower() not in ["dac", "dc", "ac"]:
            raise ValueError("'out' argument must be 'dac', 'dc', or 'ac'")
        if not isinstance(ch, int) or ch < 1 or ch > 2:
            raise ValueError("'ch' must be 1 or 2.")
        self.write(f"output{ch}:route {out}")
        if ch == 1:
            self.out1 = self.query(f"output{ch}:route?").strip()
        else:
            self.out2 = self.query(f"output{ch}:route?").strip()

    def set_amp(self, ch, amp):
        """
        Sets and reads amplitude (peak to peak value) of a given AWG channel using SCPI commands.
        Args:
            ch (int): Channel to be configured.
            amp (float): Output amplitude for channel
        """

        if not isinstance(amp, float) or amp <= 0:
            raise ValueError("'amp' must be a positive floating point value.")
        if not isinstance(ch, int) or ch < 1 or ch > 2:
            raise ValueError("'ch' must be 1 or 2.")

        if ch == 1:
            self.write(f"{self.out1}1:voltage:amplitude {amp}")
            self.amp1 = self.query(f"{self.out1}1:voltage:amplitude?")
        else:
            self.write(f"{self.out2}2:voltage:amplitude {amp}")
            self.amp2 = self.query(f"{self.out2}2:voltage:amplitude?")

    def set_func(self, ch, func):
        """
        Sets and reads function (arb/sequence) of given AWG channel using SCPI commands.
        Args:
            ch (int): Channel to be configured
            func (str): AWG function for channel ('arb', 'sts', 'stsc')
        """

        if not isinstance(ch, int) or ch < 1 or ch > 2:
            raise ValueError("'ch' must be 1 or 2.")
        if func not in ["arb", "sts", "stsc"]:
            raise ValueError("'func' must be 'arb', 'sts' (sequence), or 'stsc' (scenario).")

        self.write(f"func{ch}:mode {func}")
        if ch == 1:
            self.func1 = self.query(f"func{ch}:mode?").strip()
        else:
            self.func2 = self.query(f"func{ch}:mode?").strip()

    def set_cf(self, ch, cf):
        """
        Sets and reads center frequency of a given channel using SCPI commands.
        Args:
            ch (int): Channel to be configured
            cf (float): Carrier frequency of channel
        """

        if not isinstance(ch, int) or ch < 1 or ch > 2:
            raise ValueError("'ch' must be 1 or 2.")
        if not isinstance(cf, float) or cf <= 0:
            raise ValueError("Carrier frequency must be a positive floating point value.")
        self.write(f"carrier{ch}:freq {cf}")
        if ch == 1:
            self.cf1 = float(self.query(f"carrier{ch}:freq?").strip().split(",")[0])
        else:
            self.cf2 = float(self.query(f"carrier{ch}:freq?").strip().split(",")[0])

    def set_refSrc(self, refSrc):
        """
        Sets and reads reference clock source using SCPI commands.
        Args:
            refSrc (str): Reference clock source ('axi', 'int', 'ext').
        """

        if refSrc.lower() not in ["axi", "int", "ext"]:
            raise ValueError("'refSrc' argument must be 'axi', 'int', or 'ext'.")

        self.write(f"roscillator:source {refSrc}")
        self.refSrc = self.query("roscillator:source?").strip()

    def set_refFreq(self, refFreq):
        """
        Sets and reads reference frequency using SCPI commands.
        Args:
            refFreq (float): Reference clock frequency
        """

        if not isinstance(refFreq, float) or refFreq <= 0:
            raise ValueError("Reference frequency must be a positive floating point value.")

        self.write(f"roscillator:frequency {refFreq}")
        self.refFreq = float(self.query("roscillator:frequency?").strip())

    def set_resolution(self, res="wsp"):
        """
        Sets and reads resolution based on user input using SCPI commands.
        Args:
            res (str): DAC resolution of AWG ('wsp', 'wpr', 'intx3', 'intx12', 'intx24', 'intx48')
        """

        if res.lower() not in ["wsp", "wpr", "intx3", "intx12", "intx24", "intx48"]:
            raise ValueError("res must be 'wsp', 'wpr', 'intx3', 'intx12', 'intx24', or 'intx48'.")

        self.write(f"trace1:dwidth {res}")
        self.res = self.query("trace1:dwidth?").strip().lower()
        self.check_resolution()

    def check_resolution(self):
        """
        HELPER FUNCTION
        Populates waveform formatting constants based on 'res' (DAC resolution) attribute.
        """

        # 'wpr' = Performance (14 bit)
        if self.res == "wpr":
            self.gran = 48
            self.minLen = 240
            self.binMult = 8191
            self.binShift = 2
        # 'wsp' = Speed (12 bits)
        elif self.res == "wsp":
            self.gran = 64
            self.minLen = 320
            self.binMult = 2047
            self.binShift = 4
        # 'intxX' = Digital Upconverter (DUC) (also 14 bits)
        elif "intx" in self.res:
            # Granularity, min length, and binary format are the same for all interpolated modes.
            self.gran = 24
            self.minLen = 120
            self.binMult = 16383
            self.binShift = 1
            self.intFactor = int(self.res.split("x")[-1])
            # THIS IS IMPORTANT. If using the DUC, 'bbfs' should be used rather than 'fs' when creating waveforms.
            self.bbfs = self.fs / self.intFactor
            if self.intFactor == 3:
                self.idleGran = 8
            elif self.intFactor == 12:
                self.idleGran = 2
            elif self.intFactor == 24 or self.intFactor == 48:
                self.idleGran = 1
        else:
            raise ValueError("res argument must be 'wsp', 'wpr', 'intx3', 'intx12', 'intx24', or 'intx48'.")

    def download_wfm(self, wfmData, ch=1, name="wfm", wfmFormat="iq", sampleMkr=0, sampleMkrLength=240, syncMkr=0, syncMkrLength=240):
        """
        Defines and downloads a waveform into the segment memory.
        Assigns a waveform name to the segment. Returns segment number.
        Args:
            wfmData (NumPy array): Waveform samples (real or complex floating point values).
            ch (int): Channel to which waveform will be downloaded.
            name (str): Optional name for waveform.
            wfmFormat (str): Format of waveform. ('real', 'iq')
            sampleMkr (int): Index of the beginning of the sample marker.
            sampleMkrLength (int): Length in samples of the sample marker
            syncMkr (int): Index of the beginning of the sync marker.
            syncMkrLength (int): Length in samples of the sync marker.

        Returns:
            (int): Segment number of the downloaded waveform. Use this as the waveform identifier for the .play() method.
        """

        # Type checking
        if not isinstance(sampleMkr, int):
            raise TypeError("sampleMkr must be an int.")
        if not isinstance(syncMkr, int):
            raise TypeError("syncMkr must be an int.")
        if not isinstance(sampleMkrLength, int):
            raise TypeError("sampleMkrLength must be an int.")
        if not isinstance(syncMkrLength, int):
            raise TypeError("syncMkrLength must be an int.")

        # Stop output before doing anything else
        self.write("abort")
        self.query("*opc?")
        # IQ format is a little complex (hahaha)
        if wfmFormat.lower() == "iq":
            if wfmData.dtype != np.complex:
                raise TypeError("Invalid wfm type. IQ waveforms must be an array of complex values.")
            else:
                i = self.check_wfm(np.real(wfmData))
                q = self.check_wfm(np.imag(wfmData))

                # Create a pulse in the sample marker waveform starting at the selected index
                sampleMkrData = np.zeros(len(i), dtype=np.int16)
                # Sync marker occupies the least significant bit of each sample of I
                sampleMkrData[sampleMkr : sampleMkr + sampleMkrLength] = 1
                i += sampleMkrData

                # Create a pulse in the sync marker waveform starting at the selected index
                syncMkrData = np.zeros(len(q), dtype=np.int16)
                # Sync marker occupies the least significant bit of each sample of Q
                syncMkrData[syncMkr : syncMkr + syncMkrLength] = 1
                q += syncMkrData

                # Interleave the I and Q arrays and adjust the length to compensate
                wfm = self.iq_wfm_combiner(i, q)
                length = len(wfm) / 2
        # Real format is straightforward
        elif wfmFormat.lower() == "real":
            wfm = self.check_wfm(wfmData)
            length = len(wfm)

            # Create a pulse in the sample marker waveform starting at the selected index
            sampleMkrData = np.zeros(length, dtype=np.int16)
            # Sync marker occupies the least significant bit in the waveform data
            sampleMkrData[sampleMkr : sampleMkr + sampleMkrLength] = 1
            
            # Create a pulse in the sync marker waveform starting at the selected index
            syncMkrData = np.zeros(length, dtype=np.int16)
            # Sync marker occupies the second least significant bit in the waveform data
            syncMkrData[syncMkr : syncMkr + syncMkrLength] = 1 << 1

            # Combine sample and sync markers into single binary value and add to waveform data
            markerData = sampleMkrData + syncMkrData
            wfm += markerData
        else:
            raise ValueError('Invalid wfmFormat chosen. Use "iq" or "real".')

        # Initialize waveform segment, populate it with data, and provide a name
        segment = int(self.query(f"trace{ch}:catalog?").strip().split(",")[-2]) + 1
        self.write(f"trace{ch}:def {segment}, {length}")
        self.write_binary_values(f"trace{ch}:data {segment}, 0, ", wfm, datatype='h')
        self.write(f'trace{ch}:name {segment},"{name}_{segment}"')

        # Use 'segment' as the waveform identifier for the .play() method.
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
    #     self.write_binary_values(f'trace{ch}:data {segment}, 0, ', iq)
    #     self.write(f'trace{ch}:name {segment},"{name}_{segment}"')
    #
    #     return segment

    @staticmethod
    def iq_wfm_combiner(i, q):
        """
        HELPER FUNCTION
        Interleaves i and q wfms into a single array for download to AWG.
        Args:
            i (NumPy array): Array of real waveform samples.
            q (NumPy array): Array of imaginary waveform samples.

        Returns:
            (NumPy array): Array of interleaved IQ values.
        """

        iq = np.empty(2 * len(i), dtype=np.int16)
        iq[0::2] = i
        iq[1::2] = q
        return iq

    def check_wfm(self, wfm):
        """
        HELPER FUNCTION
        Checks minimum size and granularity and returns waveform with
        appropriate binary formatting based on the chosen DAC resolution.

        See pages 273-274 in Keysight M8190A User's Guide (Edition 13.0,
        October 2017) for more info.
        Args:
            wfm (NumPy array): Unscaled/unformatted waveform data.

        Returns:
            (NumPy array): Waveform data that has been scaled and
                formatted appropriately for download to AWG
        """

        self.check_resolution()

        # If waveform length doesn't meet granularity or minimum length requirements, repeat the waveform until it does
        repeats = wraparound_calc(len(wfm), self.gran, self.minLen)
        wfm = np.tile(wfm, repeats)
        rl = len(wfm)
        if rl < self.minLen:
            raise error.InstrumentError(f"Waveform length: {rl}, must be at least {self.minLen}.")
        rem = rl % self.gran
        if rem != 0:
            raise error.GranularityError(f"Waveform must have a granularity of {self.gran}. Extra samples: {rem}")

        # Apply the binary multiplier, cast to int16, and shift samples over if required
        return np.array(self.binMult * wfm, dtype=np.int16) << self.binShift

    def delete_segment(self, wfmID=1, ch=1):
        """
        Deletes specified waveform segment.
        Args:
            wfmID (int): Waveform identifier, used to select waveform to be deleted.
            ch (int): AWG channel from which the segment will be deleted.
        """

        # Argument checking
        if type(wfmID) != int or wfmID < 1:
            raise error.InstrumentError("Segment ID must be a positive integer.")
        if ch not in [1, 2]:
            raise error.InstrumentError("Channel must be 1 or 2.")
        self.write("abort")
        self.write(f"trace{ch}:delete {wfmID}")

    def clear_all_wfm(self):
        """Clears all segments from segment memory."""
        self.write("abort")
        self.write("trace1:delete:all")
        self.write("trace2:delete:all")

    def play(self, wfmID=1, ch=1):
        """
        Selects waveform, turns on analog output, and begins continuous playback.
        Args:
            wfmID (int): Waveform identifier, used to select waveform to be played.
            ch (int): AWG channel out of which the waveform will be played.
        """

        self.write("abort")
        self.write(f"trace{ch}:select {wfmID}")
        self.write(f"output{ch}:norm on")
        self.write("init:cont on")
        self.write("init:imm")
        self.query("*opc?")

    def play_sequence(self, ch=1):
        """
        Turns on sequence mode, selects sequence 0, turns on analog output, and begins playback.
        Args:
            ch (int): AWG channel out of which the sequence will be played.
        """

        self.write("abort")
        self.write(f"stable{ch}:sequence:select 0")
        self.write(f"output{ch}:norm on")
        self.write("init:cont on")
        self.write("init:imm")
        self.query("*opc?")

    def stop(self, ch=1):
        """
        Turns off analog output and stops playback.
        Args:
            ch (int): AWG channel to be deactivated.
        """

        self.write(f"output{ch}:norm off")
        self.write("abort")

    def create_sequence(self, numSteps, ch=1):
        """
        Deletes all sequences and creates a new sequence.
        Args:
            numSteps (int): Number of steps in the sequence. Max is 512k.
            ch (int): Channel for which sequence is created (values are 1 or 2, default is 1).
        """

        if ch not in [1, 2]:
            raise ValueError("ch argument must be 1 or 2.")
        if not isinstance(numSteps, int):
            raise TypeError("numSteps must be an int.")
        if numSteps > (2 ** 19 - 1):
            raise ValueError(f"numSteps must be less than {2**19 - 1}.")

        # Delete all sequences
        self.write(f"sequence{ch}:delete:all")

        # Create new sequence with specified number of steps.
        seqReturn = self.query(f"sequence{ch}:define:new? {numSteps}")

    def insert_wfm_in_sequence(
        self,
        wfmID,
        seqIndex,
        seqStart=False,
        seqEnd=False,
        markerEnable=False,
        segAdvance="auto",
        seqAdvance="auto",
        loopCount=1,
        startOffset=0,
        endOffset=0xFFFFFFFF,
        ch=1,
    ):
        """
        Inserts a specific waveform segment to a specific index in the sequence.
        Args:
            wfmID (int): Identifier/number of the segment to be added to the sequence.
            seqIndex (int): Index in the sequence where the segment should be added.
            seqStart (bool): Determines if this segment is the start of the sequence.
            seqEnd (bool): Determines if this segment is the end of the sequence.
            markerEnable (bool): Enables or disables the marker for this segment.
            segAdvance (str): Defines segment advance behavior. 'auto', 'conditional', 'repeat', 'single'.
            loopCount (int): Determines how many times this segment will be repeated.
            startOffset (int): Determines the start offset of the waveform in samples if only a part of the waveform is to be used. Default is 0 and should likely remain that way.
            endOffset (int): Determines the end offset of the waveform in samples if only a part of the waveform is to be used. Default is the hex value 0xffffffff and should likely remain that way.
            Note that endOffset is zero-indexed, so if you want an offset of 1000, use 999.
            ch (int): Channel for which sequence is created (values are 1 or 2, default is 1).
        """

        """
        Command Documentation
        Load sequence index with wfm segment
        stable:data <seq_id> <seq_table_index>, <control_entry>, <seq_loop_cnt>, <seg_loop_cnt>, <seg_id>, <seg_start>, <seg_end>
        Load sequence index with idle waveform
        stable:data <seq_id> <seq_table_index>, <control_entry>, <seq_loop_cnt>, <command_code>, <idle_sample>, <idle_delay>, 0
        Descriptions of the command arguments (<control_entry>, <seq_loop_cnt>, etc.) can be found
        on pages 262-265 in Keysight M8190A User's Guide (Edition 13.0, October 2017).
        """

        # Argument checking
        if ch not in [1, 2]:
            raise ValueError("ch argument must be 1 or 2.")
        if not isinstance(wfmID, int) or wfmID < 1:
            raise ValueError("wfmID must be a nonzero integer.")

        # Get length of the sequence for seqIndex checking
        cat = self.query(f"sequence{ch}:catalog?")
        seqLength = int(cat.strip().split(",")[1])

        if not isinstance(seqIndex, int) or seqIndex < 0 or seqIndex > seqLength:
            raise ValueError("seqIndex must be a nonnegative integer that is less than seqLength.")

        if not isinstance(seqStart, bool):
            raise TypeError("seqStart must be True or False.")

        if not isinstance(seqEnd, bool):
            raise TypeError("seqEnd must be True or False.")

        if not isinstance(markerEnable, bool):
            raise TypeError("markerEnable must be True or False.")

        if not isinstance(segAdvance, str) or segAdvance.lower() not in [
            "auto",
            "conditional",
            "repeat",
            "single",
        ]:
            raise ValueError("segAdvance must be 'auto', 'conditional', 'repeat', or 'single'.")

        if not isinstance(seqAdvance, str) or seqAdvance.lower() not in [
            "auto",
            "conditional",
            "repeat",
            "single",
        ]:
            raise ValueError("seqAdvance must be 'auto', 'conditional', 'repeat', or 'single'.")

        if not isinstance(loopCount, int) or loopCount < 1 or loopCount > (4 * 2 ** 30 - 1):
            raise ValueError("loopCount must be an integer between 1 and 4294967295.")

        if not isinstance(startOffset, int) or startOffset % self.gran != 0:
            raise ValueError(f"startOffset must be an integer and must obey granularity requirements. i.e. must be divisible by {self.gran}.")

        if not isinstance(endOffset, int) or (endOffset != 0xFFFFFFFF and (endOffset + 1) % self.gran != 0):
            raise ValueError(f"endOffset must be an integer and must obey granularity requirements. i.e. must be divisible by {self.gran}. It's also zero-indexed, which can cause confusion.")

        # Convert input arguments into binary for the control_sequence argument for the STABLE:DATA SCPI command
        if segAdvance.lower() == "auto":
            segAdvanceBin = 0 << 16
        elif segAdvance.lower() == "conditional":
            segAdvanceBin = 1 << 16
        elif segAdvance.lower() == "repeat":
            segAdvanceBin = 2 << 16
        elif segAdvance.lower() == "single":
            segAdvanceBin = 3 << 16

        if seqAdvance.lower() == "auto":
            seqAdvanceBin = 0 << 20
        elif seqAdvance.lower() == "conditional":
            seqAdvanceBin = 1 << 20
        elif seqAdvance.lower() == "repeat":
            seqAdvanceBin = 2 << 20
        elif seqAdvance.lower() == "single":
            seqAdvanceBin = 3 << 20

        if seqStart:
            seqStartBin = 1 << 28
        else:
            seqStartBin = 0 << 28

        if seqEnd:
            seqEndBin = 1 << 30
        else:
            seqEndBin = 0 << 30

        if markerEnable:
            markerEnableBin = 1 << 24
        else:
            markerEnableBin = 0 << 24

        # Combine all individual members of control_entry and convert to integer
        controlEntry = int(segAdvanceBin | seqStartBin | seqEndBin | markerEnableBin)

        # Send the STABLE:DATA command to populate the sequence index.
        self.write(f"stable{ch}:data {seqIndex}, {controlEntry}, 1, {loopCount}, {wfmID}, {startOffset}, {endOffset}")

        self.err_check()

    def insert_idle_in_sequence(self, seqIndex, seqStart=False, idleSample=0, idleDelay=640, ch=1):
        """
        Inserts a delay segment in the sequence table.
        Args:
            seqIndex (int): Index in the sequence where the segment should be added.
            seqStart (bool): Determines if this segment is the beginning of the sequence.
            idleSample (float): Sample value to be used as the DAC output during the idle time. Default is 0.
            idleDelay (int): Duration of delay in samples. Default (and minimum) is waveform granularity * 10. Max is (2^25 * gran) + (gran - 1).
            ch (int): Channel for which sequence is created (values are 1 or 2, default is 1).
        """

        # Input checking
        if ch not in [1, 2]:
            raise ValueError("ch argument must be 1 or 2.")

        # Get length of the sequence for seqIndex checking
        cat = self.query(f"sequence{ch}:catalog?")
        seqLength = int(cat.strip().split(",")[1])

        if not isinstance(seqIndex, int) or seqIndex < 0 or seqIndex > seqLength:
            raise ValueError("seqIndex must be a nonnegative integer that is less than seqLength.")

        if not isinstance(seqStart, bool):
            raise TypeError("seqStart must be True or False.")

        if not isinstance(idleSample, (int, float, complex)):
            raise TypeError("idleSample must be a valid waveform sample value. It is usually 0 or 0 + 1j*0 for complex waveforms.")
        if not isinstance(idleDelay, int) or idleDelay < self.gran * 10 or idleDelay > ((2 ** 25 * self.gran) + (self.gran - 1)):
            raise ValueError("idleDelay must be an integer value between gran * 10 and (2^25 * gran) + (gran - 1).")

        # Convert input arguments to the appropriate binary values
        if seqStart:
            seqStartBin = 1 << 28
        else:
            seqStartBin = 0 << 28

        # The (1 << 31) indicates that this is an idle segment.
        controlEntry = int(seqStartBin | (1 << 31))

        # Populate the sequence index with an idle segment
        self.write(f"stable1:data {seqIndex}, {controlEntry}, 1, 0, {idleSample}, {idleDelay}, 0")

        self.err_check()


# noinspection PyUnusedLocal,PyUnusedLocal
class M8195A(SignalGeneratorBase):
    """
    Generic class for controlling Keysight M8195A AWG.

    Attributes:
        dacMode (str): DAC operation mode. ('single', 'dual', 'four', 'marker', 'dcd', 'dcmarker')
        memDiv (int): Clock/memory divider rate. (1, 2, 4)
        fs (float): AWG sample rate.
        refSrc (str): Reference clock source. ('axi', 'int', 'ext')
        refFreq (float): Reference clock frequency.
        amp1/2/3/4 (float): Output amplitude in volts pk-pk. (min=75 mV, max=1 V)
        func (str): AWG mode, either arb or sequencing. ('arb', 'sts', 'stsc')

    TODO
        Add check to ensure that the correct instrument is connected
    """

    def __init__(self, ipAddress, apiType="socketscpi", timeout=10, reset=False, **kwargs):
        super().__init__(ipAddress, apiType=apiType, timeout=timeout, **kwargs)
        
        if reset:
            self.write("*rst")
            self.query("*opc?")
            self.write("abort")

        # Query all settings from AWG and store them as class attributes
        self.dacMode = self.query("inst:dacm?").strip()
        self.memDiv = 1
        self.fs = float(self.query("frequency:raster?").strip())
        self.effFs = self.fs / self.memDiv
        self.func = self.query("func:mode?").strip()
        self.refSrc = self.query("roscillator:source?").strip()
        self.refFreq = float(self.query("roscillator:frequency?").strip())
        self.amp1 = float(self.query("voltage1?"))
        self.amp2 = float(self.query("voltage2?"))
        self.amp3 = float(self.query("voltage3?"))
        self.amp4 = float(self.query("voltage4?"))

        # Initialize waveform format constants and populate them with check_resolution()
        self.gran = 256
        self.minLen = 1280
        self.binMult = 127
        self.binShift = 0

    # def configure(self, dacMode='single', memDiv=1, fs=64e9, refSrc='axi', refFreq=100e6, amp1=300e-3, amp2=300e-3, amp3=300e-3, amp4=300e-3, func='arb'):
    def configure(self, **kwargs):
        """
        Sets basic configuration for M8195A and populates class attributes accordingly.
        Keyword Arguments:
            dacMode (str): DAC operation mode. ('single', 'dual', 'four', 'marker', 'dcd', 'dcmarker')
            memDiv (int): Clock/memory divider rate. (1, 2, 4)
            fs (float): AWG sample rate.
            refSrc (str): Reference clock source. ('axi', 'int', 'ext')
            refFreq (float): Reference clock frequency.
            amp1/2/3/4 (float): Output amplitude in volts pk-pk. (min=75 mV, max=1 V)
            func (str): AWG mode, either arb or sequencing. ('arb', 'sts', 'stsc')
        """

        # Stop output on all channels before doing anything else
        for ch in range(1, 5):
            self.stop(ch=ch)

        # Check to see which keyword arguments the user sent and call the appropriate function
        for key, value in kwargs.items():
            if key == "dacMode":
                self.set_dacMode(value)
            elif key == "memDiv":
                self.set_memDiv(value)
            elif key == "fs":
                self.set_fs(value)
            elif key == "refSrc":
                self.set_refSrc(value)
            elif key == "refFreq":
                self.set_refFreq(value)
            elif key == "amp1":
                self.set_amplitude(value, channel=1)
            elif key == "amp2":
                self.set_amplitude(value, channel=2)
            elif key == "amp3":
                self.set_amplitude(value, channel=3)
            elif key == "amp4":
                self.set_amplitude(value, channel=4)
            elif key == "func":
                self.set_func(value)
            else:
                raise KeyError(f'Invalid keyword argument: "{key}"')  # raise KeyError('Invalid keyword argument. Use "dacMode", "memDiv", "fs", "refSrc", "refFreq", "amp1/2/3/4", or "func".')

        self.err_check()

    def set_dacMode(self, dacMode="single"):
        """
        Sets and reads DAC mode for the M8195A using SCPI commands.
        Args:
            dacMode (str): DAC operation mode. ('single', 'dual', 'four', 'marker', 'dcd', 'dcmarker')
        """

        if dacMode not in ["single", "dual", "four", "marker", "dcd", "dcmarker"]:
            raise ValueError("'dacMode' must be 'single', 'dual', 'four', 'marker', 'dcd', or 'dcmarker'.")

        self.write(f"inst:dacm {dacMode}")
        self.dacMode = self.query("inst:dacm?").strip().lower()

    def set_memDiv(self, memDiv=1):
        """
        Sets and reads memory divider rate using SCPI commands.
        Args:
            memDiv (int): Clock/memory divider rate. (1, 2, 4)
        """

        if memDiv not in [1, 2, 4]:
            raise ValueError("Memory divider must be 1, 2, or 4.")
        self.write(f"instrument:memory:extended:rdivider div{memDiv}")
        self.memDiv = int(self.query("instrument:memory:extended:rdivider?").strip().split("DIV")[-1])

    def set_fs(self, fs=65e9):
        """
        Sets and reads sample rate using SCPI commands.
        Args:
            fs (float): AWG sample rate.
        """

        if not isinstance(fs, (int, float)) or fs <= 0:
            raise ValueError("Sample rate must be a positive floating point value.")
        self.write(f"frequency:raster {fs}")
        self.fs = float(self.query("frequency:raster?").strip())
        self.effFs = self.fs / self.memDiv

    def set_func(self, func="arb"):
        """
        Sets and reads AWG function using SCPI commands.
        Args:
            func (str): AWG mode, either arb or sequencing. ('arb', 'sts', 'stsc')
        """

        if func.lower() not in ["arb", "sts", "stsc"]:
            raise ValueError("'func' argument must be 'arb', 'sts', 'stsc'")
        self.write(f"func:mode {func}")
        self.func = self.query("func:mode?").strip()

    def set_refSrc(self, refSrc="axi"):
        """
        Sets and reads reference source using SCPI commands.
        Args:
            refSrc (str): Reference clock source. ('axi', 'int', 'ext')
        """

        if refSrc.lower() not in ["axi", "int", "ext"]:
            raise ValueError("'refSrc' must be 'axi', 'int', or 'ext'")
        self.write(f"roscillator:source {refSrc}")
        self.refSrc = self.query("roscillator:source?").strip()

    def set_refFreq(self, refFreq=100e6):
        """
        Sets and reads reference frequency using SCPI commands.
        Args:
            refFreq (float): Reference clock frequency.
        """

        if not isinstance(refFreq, float) or refFreq <= 0:
            raise ValueError("Reference frequency must be a positive floating point value.")
        self.write(f"roscillator:frequency {refFreq}")
        self.refFreq = float(self.query("roscillator:frequency?").strip())

    def set_amplitude(self, amplitude=300e-3, channel=1):
        """
        Sets and reads the output voltage amplitude (pk-pk) for specified channels using SCPI commands.
        Args:
            amplitude (float): Output amplitude in Volts pk-pk.
            channel (int): Channel to change. (1, 2, 3, or 4).
        """
        if channel not in [1, 2, 3, 4]:
            raise error.InstrumentError("'channel' must be 1, 2, 3, or 4.")
        if not isinstance(amplitude, float) and not isinstance(amplitude, int):
            raise error.InstrumentError("'amplitude' must be a floating point value.")
        if amplitude < 75e-3 or amplitude > 1:
            raise error.InstrumentError("'amplitude' must be between 75 mV and 1 V.")

        self.write(f"voltage{channel} {amplitude}")
        # This is a neat use of Python's exec() function, which takes a "program" in as a string and executes it
        # Very useful if you need to dynamically decide which variable names to call
        exec(f"self.amp{channel} = float(self.query('voltage{channel}?'))")

    def sanity_check(self):
        """Prints out user-accessible class attributes."""

        print("Sample rate:", self.fs)
        print("DAC Mode:", self.dacMode)
        print("Function:", self.func)
        print("Ref source:", self.refSrc)
        print("Ref frequency:", self.refFreq)
        print("Amplitude CH 1:", self.amp1)
        print("Amplitude CH 2:", self.amp2)
        print("Amplitude CH 3:", self.amp3)
        print("Amplitude CH 4:", self.amp4)

    def download_wfm(self, wfmData, ch=1, name="wfm", *args, **kwargs):
        """
        Defines and downloads a waveform into the segment memory.
        Assigns a waveform name to the segment. Returns segment number.
        Args:
            wfmData (NumPy array): Waveform samples (real or complex floating point values).
            ch (int): Channel to which waveform will be downloaded.
            name (str): Optional name for waveform.
            # sampleMkr (int): Index of the beginning of the sample marker.
            # syncMkr (int): Index of the beginning of the sync marker.

        Returns:
            (int): Segment number of the downloaded waveform. Use this as the waveform identifier for the .play() method.
        """

        # Stop output before doing anything else
        self.write("abort")
        wfm = self.check_wfm(wfmData)
        length = len(wfmData)

        # Initialize waveform segment, populate it with data, and provide a name
        segment = int(self.query(f"trace{ch}:catalog?").strip().split(",")[-2]) + 1
        self.write(f"trace{ch}:def {segment}, {length}")
        self.write_binary_values(f"trace{ch}:data {segment}, 0, ", wfm, datatype='b')
        self.write(f'trace{ch}:name {segment},"{name}_{segment}"')

        # Use 'segment' as the waveform identifier for the .play() method.
        return segment

    def check_wfm(self, wfmData):
        """
        HELPER FUNCTION
        Checks minimum size and granularity and returns waveform with
        appropriate binary formatting.

        See page 253 in Keysight M8195A User's Guide Rev 2 (Edition 7.0,
        March 2019) for more info.
        Args:
            wfmData (NumPy array): Unscaled/unformatted waveform data.

        Returns:
            (NumPy array): Waveform data that has been scaled and
                formatted appropriately for download to AWG
        """

        # If waveform length doesn't meet granularity or minimum length requirements, repeat the waveform until it does
        repeats = wraparound_calc(len(wfmData), self.gran, self.minLen)
        wfm = np.tile(wfmData, repeats)
        rl = len(wfm)
        if rl < self.minLen:
            raise error.InstrumentError(f"Waveform length: {rl}, must be at least {self.minLen}.")
        if rl % self.gran != 0:
            raise error.GranularityError(f"Waveform must have a granularity of {self.gran}.")

        # Apply the binary multiplier, cast to int16, and shift samples over if required
        return np.array(self.binMult * wfm, dtype=np.int8) << self.binShift

    def delete_segment(self, wfmID=1, ch=1):
        """
        Deletes specified waveform segment.
        Args:
            wfmID (int): Waveform identifier, used to select waveform to be deleted.
            ch (int): AWG channel from which the segment will be deleted.
        """

        # Argument checking
        if type(wfmID) != int or wfmID < 1:
            raise ValueError("Segment ID must be a positive integer.")
        if ch not in [1, 2, 3, 4]:
            raise ValueError("Channel must be 1, 2, 3, or 4.")
        self.write("abort")
        self.write(f"trace{ch}:del {wfmID}")

    def clear_all_wfm(self):
        """Clears all segments from segment memory."""
        self.write("abort")
        for ch in range(1, 5):
            self.write(f"trace{ch}:del:all")

    def play(self, wfmID=1, ch=1):
        """
        Selects waveform, turns on analog output, and begins continuous playback.
        Args:
            wfmID (int): Waveform identifier, used to select waveform to be played.
            ch (int): AWG channel out of which the waveform will be played.
        """

        self.write(f"trace:select {wfmID}")
        self.write(f"output{ch} on")
        self.write("init:cont on")
        self.write("init:imm")

    def stop(self, ch=1):
        """
        Turns off analog output and stops playback.
        Args:
            ch (int): AWG channel to be deactivated.
        """

        self.write(f"output{ch} off")
        self.write("abort")


# noinspection PyUnusedLocal,PyUnusedLocal
class M8196A(SignalGeneratorBase):
    """
    Generic class for controlling Keysight M8196A AWG.

    Attributes:
        dacMode (str): DAC operation mode. ('single', 'dual', 'four', 'marker', 'dcmarker')
        fs (float): AWG sample rate.
        refSrc (str): Reference clock source. ('axi', 'int', 'ext')
        refFreq (float): Reference clock frequency.

    TODO
        Add check to ensure that the correct instrument is connected
    """

    def __init__(self, ipAddress, apiType="socketscpi", timeout=10, reset=False, **kwargs):
        super().__init__(ipAddress, apiType=apiType, timeout=timeout, **kwargs)
        
        if reset:
            self.write("*rst")
            self.query("*opc?")
            self.write("abort")

        # Query all settings from AWG and store them as class attributes
        self.dacMode = self.query("inst:dacm?").strip()
        self.fs = float(self.query("frequency:raster?").strip())
        self.amp = float(self.query("voltage?").strip())
        self.refSrc = self.query("roscillator:source?").strip()
        self.refFreq = float(self.query("roscillator:frequency?").strip())

        # Initialize waveform format constants and populate them with check_resolution()
        self.gran = 128
        self.minLen = 128
        self.maxLen = 524288
        self.binMult = 127
        self.binShift = 0

    # def configure(self, dacMode='single', fs=92e9, refSrc='axi', refFreq=100e6):
    def configure(self, **kwargs):
        """
        Sets basic configuration for M8196A and populates class attributes accordingly.
        Keyword Args:
            dacMode (str): DAC operation mode. ('single', 'dual', 'four', 'marker', 'dcmarker')
            fs (float): AWG sample rate.
            refSrc (str): Reference clock source. ('axi', 'int', 'ext')
            refFreq (float): Reference clock frequency.
        """

        # Stop output before doing anything else
        self.write("abort")

        # Check to see which keyword arguments the user sent and call the appropriate function
        for key, value in kwargs.items():
            if key == "dacMode":
                self.set_dacMode(value)  # self.dacMode = self.query('inst:dacm?').strip().lower()
            elif key == "fs":
                self.set_fs(value)  # self.fs = float(self.query('frequency:raster?').strip())
            elif key == "refSrc":
                self.set_refSrc(value)
            elif key == "refFreq":
                self.set_refFreq(value)
            else:
                raise KeyError(f'Invalid keyword argument: "{key}"')  # raise KeyError('Invalid keyword argument. Use "dacMode", "fs", "refSrc", "refFreq".')

        self.err_check()

    def set_dacMode(self, dacMode="single"):
        """
        Sets and reads DAC mode for the M8196A using SCPI commands
        Args:
            dacMode (str): DAC operation mode. ('single', 'dual', 'four', 'marker', 'dcd', 'dcmarker')
        """

        if dacMode not in ["single", "dual", "four", "marker", "dcmarker"]:
            raise ValueError("Invalid DAC mode. Must be 'single', 'dual', 'four', 'marker', or 'dcmarker'")

        self.write(f"inst:dacm {dacMode}")
        self.dacMode = self.query("inst:dacm?").strip().lower()

    def set_fs(self, fs=92e9):
        """
        Sets and reads sample rate using SCPI commands.
        Args:
            fs (float): AWG sample rate.
        """

        if not isinstance(fs, (int, float)) or fs <= 0:
            raise ValueError("Sample rate must be a positive floating point value.")
        self.write(f"frequency:raster {fs}")
        self.fs = float(self.query("frequency:raster?").strip())

    def set_refSrc(self, refSrc="axi"):
        """
        Sets and reads reference source using SCPI commands.
        Args:
            refSrc (str): Reference clock source. ('axi', 'int', 'ext')
        """

        if refSrc.lower() not in ["axi", "int", "ext"]:
            raise ValueError("'refSrc' must be 'axi', 'int', or 'ext'")
        self.write(f"roscillator:source {refSrc}")
        self.refSrc = self.query("roscillator:source?").strip()

    def set_refFreq(self, refFreq=100e6):
        """
        Sets and reads reference frequency using SCPI commands.
        Args:
            refFreq (float): Reference clock frequency.
        """

        # Check for valid refSrc arguments and assign
        if self.refSrc.lower() not in ["int", "ext", "axi"]:
            raise error.InstrumentError("Invalid reference source selection.")
        self.write(f"roscillator:source {self.refSrc}")
        self.refSrc = self.query("roscillator:source?").strip().lower()

        # Check for presence of external ref signal
        srcAvailable = self.query(f"roscillator:source:check? {self.refSrc}").strip()
        if not srcAvailable:
            raise error.InstrumentError("No signal at selected reference source.")

        # Only set ref frequency if using ext ref, int/axi is always 100 MHz
        if self.refSrc == "ext":
            # Seamlessly manage external clock range selection based on ref freq.
            # Precision clock source
            if 2.3125e9 <= refFreq <= 3e9:
                self.write("roscillator:range rang3")
            # Standard external clock source
            elif 10e6 <= refFreq <= 300e6:
                self.write("roscillator:range rang1")
            # Wide external clock source
            elif 162e6 <= refFreq <= 17e9:
                self.write("roscillator:range rang2")
            else:
                raise error.InstrumentError("Selected reference clock frequency outside allowable range.")
            self.write(f"roscillator:frequency {refFreq}")
        self.refFreq = float(self.query("roscillator:frequency?").strip())

    def sanity_check(self):
        """Prints out user-accessible class attributes."""

        print("Sample rate:", self.fs)
        print("DAC Mode:", self.dacMode)
        print("Ref source:", self.refSrc)
        print("Ref frequency:", self.refFreq)

    def download_wfm(self, wfmData, ch=1, name="wfm", *args, **kwargs):
        """
        Defines and downloads a waveform into the segment memory.
        Assigns a waveform name to the segment. Returns segment number.
        Args:
            wfmData (NumPy array): Waveform samples (real or complex floating point values).
            ch (int): Channel to which waveform will be downloaded.
            name (str): Optional name for waveform.
            # sampleMkr (int): Index of the beginning of the sample marker.
            # syncMkr (int): Index of the beginning of the sync marker.

        Returns:
            (int): Segment number of the downloaded waveform. Use this as the waveform identifier for the .play() method.
        """

        # Stop output before doing anything else
        self.write("abort")
        self.clear_all_wfm()
        wfm = self.check_wfm(wfmData)
        length = len(wfm)

        # Initialize waveform segment, populate it with data, and provide a name
        segment = 1
        self.write(f"trace{ch}:def {segment}, {length}")
        self.write_binary_values(f"trace{ch}:data {segment}, 0, ", wfm, datatype='b')
        self.write(f'trace{ch}:name {segment},"{name}_{segment}"')

        # Use 'segment' as the waveform identifier for the .play() method.
        return segment

    def check_wfm(self, wfmData):
        """
        HELPER FUNCTION
        Checks minimum size and granularity and returns waveform with
        appropriate binary formatting.

        See page 132 in Keysight M8196A User's Guide (Edition 2.2,
        March 2018) for more info.
        Args:
            wfmData (NumPy array): Unscaled/unformatted waveform data.

        Returns:
            (NumPy array): Waveform data that has been scaled and
                formatted appropriately for download to AWG
        """

        # If waveform length doesn't meet granularity or minimum length requirements, repeat the waveform until it does
        repeats = wraparound_calc(len(wfmData), self.gran, self.minLen)
        wfm = np.tile(wfmData, repeats)
        rl = len(wfm)
        if rl < self.minLen:
            raise error.InstrumentError(f"Waveform length: {rl}, must be at least {self.minLen}.")
        if rl > self.maxLen:
            raise error.InstrumentError(f"Waveform length: {rl}, must be shorter than {self.maxLen}.")
        if rl % self.gran != 0:
            raise error.GranularityError(f"Waveform must have a granularity of {self.gran}.")

        # Apply the binary multiplier, cast to int16, and shift samples over if required
        return np.array(self.binMult * wfm, dtype=np.int8) << self.binShift

    def delete_segment(self):
        """Deletes waveform segment (M8196A only has one)."""
        self.clear_all_wfm()

    def clear_all_wfm(self):
        """Clears all segments from segment memory."""
        self.write("abort")
        for ch in range(1, 5):
            self.write(f"trace{ch}:del:all")

    def play(self, ch=1):
        """
        Selects waveform, turns on analog output, and begins continuous playback.
        Args:
            ch (int): AWG channel out of which the waveform will be played.
        """

        self.write(f"output{ch}:state on")
        self.write("init:cont on")
        self.write("init:imm")

    def stop(self, ch=1):
        """
        Turns off analog output and stops playback.
        Args:
            ch (int): AWG channel to be deactivated.
        """

        self.write("abort")
        self.write(f"output{ch}:state off")


# noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
class VSG(SignalGeneratorBase):
    def __init__(self, ipAddress, apiType="socketscpi", timeout=10, reset=False, **kwargs):
        """
        Generic class for controlling the EXG, MXG, PSG, and M938X
        family signal generators.

        Attributes:
            rfState (int): Turns the RF output on or off. (1, 0)
            modState (int): Turns the baseband modulator on or off. (1, 0)
            cf (float): Sets the generator's carrier frequency.
            amp (int/float): Sets the generator's RF output power.
            alcState (int): Turns the ALC (automatic level control) on or off. (1, 0)
            iqScale (int): Scales the IQ modulator. Default/safe value is 70
            refSrc (str): Sets the reference clock source. ('int', 'ext', 'bbg')
            fs (float): Sets the sample rate of the baseband generator.

        TODO
            Add check to ensure that the correct instrument is connected
        """

        super().__init__(ipAddress, apiType=apiType, timeout=timeout, **kwargs)
        if reset:
            self.write("*rst")
            self.query("*opc?")

        # Query all settings from VSG and store them as class attributes
        self.rfState = self.query("output?").strip()
        self.modState = self.query("output:modulation?").strip()
        self.cf = float(self.query("frequency?").strip())
        self.amp = float(self.query("power?").strip())
        self.alcState = self.query("power:alc?".strip())
        self.refSrc = self.query("roscillator:source?").strip()
        self.arbState = self.query("radio:arb:state?").strip()
        self.fs = float(self.query("radio:arb:sclock:rate?").strip())
        if "int" in self.refSrc.lower():
            self.refFreq = 10e6
        elif "ext" in self.refSrc.lower():
            self.refFreq = float(self.query("roscillator:frequency:external?").strip())
        elif "bbg" in self.refSrc.lower():
            if "M938" not in self.instId:
                self.refFreq = float(self.query("roscillator:frequency:bbg?").strip())
            else:
                raise error.InstrumentError("Invalid reference source chosen, select 'int' or 'ext'.")
        else:
            raise error.InstrumentError("Unknown refSrc selected.")

        # Initialize waveform format constants and populate them with check_resolution()
        self.minLen = 60
        self.binMult = 32767
        if "M938" not in self.instId:
            self.iqScale = float(self.query("radio:arb:rscaling?").strip())
            self.gran = 2
        else:
            self.gran = 4

    # def configure(self, rfState=1, modState=1, cf=1e9, amp=-20, alcState=0, iqScale=70, refSrc='int', fs=200e6):
    def configure(self, **kwargs):
        """
        Sets basic configuration for VSG and populates class attributes accordingly.
        Keyword Arguments:
            rfState (int): Turns the RF output on or off. (1, 0)
            modState (int): Turns the baseband modulator on or off. (1, 0)
            cf (float): Sets the generator's carrier frequency.
            amp (int/float): Sets the generator's RF output power.
            alcState (int): Turns the ALC (automatic level control) on or off. (1, 0)
            iqScale (int): Scales the IQ modulator. Default/safe value is 70
            refSrc (str): Sets the reference clock source. ('int', 'ext', 'bbg')
            fs (float): Sets the sample rate of the baseband generator.
        """

        # Check to see which keyword arguments the user sent and call the appropriate function
        for key, value in kwargs.items():
            if key == "rfState":
                self.set_rfState(value)
            elif key == "modState":
                self.set_modState(value)
            elif key == "cf":
                self.set_cf(value)
            elif key == "amp":
                self.set_amp(value)
            elif key == "alcState":
                self.set_alcState(value)
            elif key == "iqScale":
                self.set_iqScale(value)
            elif key == "refSrc":
                self.set_refSrc(value)
            elif key == "fs":
                self.set_fs(value)
            else:
                raise KeyError(f'Invalid keyword argument: "{key}"')  # raise KeyError('Invalid keyword argument.')

        # Arb state can only be turned on after a waveform has been loaded/selected
        # self.write(f'radio:arb:state {arbState}')
        # self.arbState = self.query('radio:arb:state?').strip()

        self.err_check()

    def set_rfState(self, rfState):
        """
        Sets and reads the state of the RF output using SCPI commands.
        Args:
            rfState (int): Turns the RF output on or off. (1, 0)
        """

        if rfState not in [1, 0, "on", "off", "ON", "OFF", "On", "Off"]:
            raise ValueError('"rfState" should be 1, 0, "on", or "off"')

        self.write(f"output {rfState}")
        self.rfState = int(self.query("output?").strip())

    def set_modState(self, modState):
        """
        Sets and reads the state of the internal baseband modulator output using SCPI commands.
        Args:
            modState (int): Turns the baseband modulator on or off. (1, 0)
        """

        if modState not in [1, 0, "on", "off", "ON", "OFF", "On", "Off"]:
            raise ValueError('"modState" should be 1, 0, "on", or "off"')

        self.write(f"output:modulation {modState}")
        self.modState = int(self.query("output:modulation?").strip())

    def set_arbState(self, arbState):
        """
        Sets and reads the state of the internal arb waveform generator using SCPI commands.
        Args:
            arbState (int): Turns the arb waveform generator on or off. (1, 0)
        """

        if arbState not in [1, 0, "on", "off", "ON", "OFF", "On", "Off"]:
            raise ValueError('"arbState" should be 1, 0, "on", or "off"')

        self.write(f"radio:arb:state {arbState}")
        self.arbState = int(self.query("radio:arb:state?").strip())

    def set_cf(self, cf):
        """
        Sets and reads the center frequency of the signal generator output using SCPI commands.
        Args:
            cf (float): Sets the generator's carrier frequency.
        """

        if not isinstance(cf, float) or cf <= 0:
            raise ValueError("Carrier frequency must be a positive floating point value.")
        self.write(f"frequency {cf}")
        self.cf = float(self.query("frequency?").strip())

    def set_amp(self, amp):
        """
        Sets and reads the output amplitude of signal generator output using SCPI commands.
        Args:
            amp (int/float): Sets the generator's RF output power.
        """

        if not isinstance(amp, (float, int)):
            raise ValueError("Amp argument must be a numerical value.")
        self.write(f"power {amp}")
        self.amp = float(self.query("power?").strip())

    def set_alcState(self, alcState):
        """
        Sets and reads the state of the ALC (automatic level control) output using SCPI commands.
        This should be turned off for narrow pulses and signals with rapid amplitude changes.
        Args:
            alcState (int): Turns the ALC (automatic level control) on or off. (1, 0)
        """

        if alcState not in [1, 0, "on", "off", "ON", "OFF", "On", "Off"]:
            raise ValueError('"rfState" should be 1, 0, "on", or "off"')

        self.write(f"power:alc {alcState}")
        self.alcState = int(self.query("power:alc?").strip())

    def set_iqScale(self, iqScale):
        """
        Sets and reads the scaling of the baseband IQ waveform output using SCPI commands.
        Should be about 70 percent to avoid clipping.
        Args:
            iqScale (int): Scales the IQ modulator in percent. Default/safe value is 70, range is 0 to 100.
        """

        if not isinstance(iqScale, int) or iqScale <= 0 or iqScale > 100:
            raise ValueError("iqScale argument must be an integer between 1 and 100.")

        # M9381/3A don't have an IQ scaling command.
        if "M938" not in self.instId:
            self.write(f"radio:arb:rscaling {iqScale}")
            self.iqScale = float(self.query("radio:arb:rscaling?").strip())

    def set_fs(self, fs):
        """
        Sets and reads sample  rate of internal arb output using SCPI commands.
        Args:
            fs (float): Sample rate.
        """

        if not isinstance(fs, (int, float)) or fs <= 0:
            raise ValueError("Sample rate must be a positive floating point value.")
        self.write(f"radio:arb:sclock:rate {fs}")
        self.fs = float(self.query("radio:arb:sclock:rate?").strip())

    def set_refSrc(self, refSrc):
        """
        Sets and reads the reference clock source output using SCPI commands.
        Args:
            refSrc (str): Sets the reference clock source. ('int', 'ext', 'bbg')
        """

        if not isinstance(refSrc, str) or refSrc.lower() not in [
            "int",
            "ext",
            "internal",
            "external",
            "bbg",
        ]:
            raise ValueError('"refSrc" must be "internal", "external", or "bbg".')

        self.write(f"roscillator:source {refSrc}")
        self.refSrc = self.query("roscillator:source?").strip()
        if "int" in self.refSrc.lower():
            self.refFreq = 10e6
        elif "ext" in self.refSrc.lower():
            self.refFreq = float(self.query("roscillator:frequency:external?").strip())
        elif "bbg" in self.refSrc.lower():
            self.refFreq = float(self.query("roscillator:frequency:bbg?").strip())
        else:
            raise error.InstrumentError("Unknown refSrc selected.")

    def sanity_check(self):
        """Prints out user-accessible class attributes."""
        print("RF State:", self.rfState)
        print("Modulation State:", self.modState)
        print("Center Frequency:", self.cf)
        print("Output Amplitude:", self.amp)
        print("ALC state:", self.alcState)
        print("Reference Source:", self.refSrc)
        print("Internal Arb State:", self.arbState)
        print("Internal Arb Sample Rate:", self.fs)
        if "M938" not in self.instId:
            print("IQ Scaling:", self.iqScale)

    def download_wfm(self, wfmData, wfmID="wfm"):
        """
        Defines and downloads a waveform into the waveform memory.
        Returns useful waveform identifier.
        Args:
            wfmData (NumPy array): Complex waveform values.
            wfmID (str): Waveform name.

        Returns:
            (str): Useful waveform identifier/name. Use this as the waveform identifier for the .play() method.
        """

        # Stop output before doing anything else
        self.set_modState(0)
        self.set_arbState(0)

        # # Adjust endianness for M9381/3A
        if "M938" in self.instId:
            bigEndian = False
        else:
            bigEndian = True

        # Data type checking
        if not isinstance(wfmData, np.ndarray):
            raise TypeError("wfmData should be a complex NumPy array.")

        # Waveform format checking. VSGs can only use 'iq' format waveforms.
        if wfmData.dtype != complex:
            raise TypeError("Invalid wfm type. IQ waveforms must be an array of complex values.")
        else:
            i = self.check_wfm(np.real(wfmData), bigEndian=bigEndian)
            q = self.check_wfm(np.imag(wfmData), bigEndian=bigEndian)

            wfm = self.iq_wfm_combiner(i, q)

        # M9381/3A download procedure is slightly different from X-series sig gens
        if "M938" in self.instId:
            try:
                self.write(f'memory:delete "{wfmID}"')
                self.query("*opc?")
                self.write(f'mmemory:delete "C:\\Temp\\{wfmID}"')
                self.query("*opc?")
                self.err_check()
            except socketscpi.SockInstError:
                # print('Waveform doesn\'t exist, skipping delete operation.')
                pass
            self.write_binary_values(f'mmemory:data "C:\\Temp\\{wfmID}",', wfm, datatype='h')
            self.write(f'memory:copy "C:\\Temp\\{wfmID}","{wfmID}"')

        # EXG/MXG/PSG download procedure
        else:
            self.write_binary_values(f'mmemory:data "WFM1:{wfmID}",', wfm, datatype='h')
            self.write(f'radio:arb:waveform "WFM1:{wfmID}"')

        # Use 'wfmID' as the waveform identifier for the .play() method.
        return wfmID

    @staticmethod
    def iq_wfm_combiner(i, q):
        """
        HELPER FUNCTION
        Combines i and q wfms into a single interleaved wfm for download to generator.
        Args:
            i (NumPy array): Array of real waveform samples.
            q (NumPy array): Array of imaginary waveform samples.

        Returns:
            (NumPy array): Array of interleaved IQ values.
        """

        iq = np.empty(2 * len(i), dtype=np.int16)
        iq[0::2] = i
        iq[1::2] = q
        return iq

    def check_wfm(self, wfm, bigEndian=True):
        """
        HELPER FUNCTION
        Checks minimum size and granularity and returns waveform with
        appropriate binary formatting. Note that sig gens expect big endian
        byte order.

        See pages 205-256 in Keysight X-Series Signal Generators Programming
        Guide (November 2014 Edition) for more info.
        Args:
            wfm (NumPy array): Unscaled/unformatted waveform data.
            bigEndian (bool): Determines whether waveform is big endian.

        Returns:
            (NumPy array): Waveform data that has been scaled and
                formatted appropriately for download to AWG
        """

        # If waveform length doesn't meet granularity or minimum length requirements, repeat the waveform until it does
        repeats = wraparound_calc(len(wfm), self.gran, self.minLen)
        wfm = np.tile(wfm, repeats)
        rl = len(wfm)
        if rl < self.minLen:
            raise error.InstrumentError(f"Waveform length: {rl}, must be at least {self.minLen}.")
        if rl % self.gran != 0:
            raise error.GranularityError(f"Waveform must have a granularity of {self.gran}.")

        if bigEndian:
            return np.array(self.binMult * wfm, dtype=np.int16).byteswap()
        else:
            return np.array(self.binMult * wfm, dtype=np.int16)

    def delete_wfm(self, wfmID):
        """
        Stops output and deletes specified waveform.
        Args:
            wfmID (str): Name of waveform to be deleted.
        """

        self.stop()
        if "M938" in self.instId:
            self.write(f'memory:delete "{wfmID}"')
        else:
            self.write(f'memory:delete "WFM1:{wfmID}"')
        self.err_check()

    def clear_all_wfm(self):
        """Stops output and deletes all iq waveforms."""
        self.stop()
        if "M938" in self.instId:
            """UNTESTED PLEASE TEST"""
            self.write("memory:delete:all")
        else:
            self.write("mmemory:delete:wfm")
        self.err_check()

    def play(self, wfmID="wfm"):
        """
        Selects waveform and activates arb mode, RF output, and modulation.
        Args:
            wfmID (str): Waveform identifier, used to select waveform to be played.
        """

        # Waveform selection is slightly different between PXIe and standalone sig gens.
        if "M938" in self.instId:
            self.write(f'radio:arb:waveform "{wfmID}"')
        else:
            self.write(f'radio:arb:waveform "WFM1:{wfmID}"')

        self.set_rfState(1)
        self.set_modState(1)
        self.set_arbState(1)
        self.err_check()

    def stop(self):
        """Dectivates arb mode, RF output, and modulation."""

        self.set_rfState(0)
        self.set_modState(0)
        self.set_arbState(0)


# noinspection PyAttributeOutsideInit,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
class VXG(SignalGeneratorBase):
    # def __init__(self, host, port=5025, timeout=10, reset=False):
    def __init__(self, ipAddress, apiType="socketscpi", timeout=10, reset=False, **kwargs):

        """
        Generic class for controlling the M9384B VXG signal generator.

        Attributes:
            rf1State (int): Turns the RF output on or off. (1, 0)
            modState (int): Turns the baseband modulator on or off. (1, 0)
            cf (float): Sets the generator's carrier frequency.
            amp (int/float): Sets the generator's RF output power.
            alcState (int): Turns the ALC (automatic level control) on or off. (1, 0)
            iqScale (int): Scales the IQ modulator. Default/safe value is 70
            refSrc (str): Sets the reference clock source. ('int', 'ext', 'bbg')
            fs (float): Sets the sample rate of the baseband generator.

        TODO
            Add check to ensure that the correct instrument is connected
        """

        # super().__init__(host, port, timeout)
        super().__init__(ipAddress, apiType=apiType, timeout=timeout, **kwargs)
        if reset:
            self.write("*rst")
            self.query("*opc?")

        # Query the options on the VXG to see how many channels it has
        optionString = self.query("*opt?")

        # Query all settings from VXG and store them as class attributes
        self.rfState1 = self.query("rf1:output?").strip()
        self.modState1 = self.query("rf1:output:modulation?").strip()
        self.cf1 = float(self.query("source:rf1:frequency?").strip())
        self.amp1 = float(self.query("rf1:power?").strip())
        self.arbState1 = self.query("signal1:state?").strip()
        self.alcState1 = self.query("rf1:power:alc?")
        self.iqScale1 = float(self.query("source:signal1:waveform:scale?").strip())
        self.rms1 = float(self.query("source:signal1:waveform:rms?").strip())
        self.fs1 = float(self.query("signal1:waveform:sclock:rate?").strip())

        # If there are two channels, repeat the queries above for the second channel
        if "002" in optionString:
            self.numCh = 2
            self.rfState2 = self.query("rf2:output?").strip()
            self.modState2 = self.query("rf2:output:modulation?").strip()
            self.cf2 = float(self.query("source:rf2:frequency?").strip())
            self.amp2 = float(self.query("rf2:power?").strip())
            self.arbState2 = self.query("signal2:state?").strip()
            self.alcState2 = self.query("rf2:power:alc?")
            self.iqScale2 = float(self.query("source:signal2:waveform:scale?").strip())
            self.rms2 = float(self.query("source:signal2:waveform:rms?").strip())
            self.fs2 = float(self.query("signal2:waveform:sclock:rate?").strip())
        else:
            self.numCh = 1

        # Reference source settings are independent of channel number.
        self.refSrc = self.query("roscillator:source?").strip()

        if "int" in self.refSrc.lower():
            self.refFreq = 10e6
        elif "ext" in self.refSrc.lower():
            self.refFreq = float(self.query("roscillator:frequency:external?").strip())
        else:
            raise error.InstrumentError("Unknown refSrc selected.")

        # Initialize waveform format constants and populate them with check_resolution()
        self.minLen = 512
        self.binMult = 32767
        self.gran = 8

    # def configure(self, rfState=1, modState=1, cf=1e9, amp=-20, alcState=0, iqScale=70, refSrc='int', fs=200e6):
    def configure(self, **kwargs):
        """
        Sets basic configuration for VXG and populates class attributes accordingly.
        Keyword Arguments:
            rfState1|2 (int): Turns the RF output on or off. (1, 0)
            modState1|2 (int): Turns the baseband modulator on or off. (1, 0)
            cf1|2 (float): Sets the generator's carrier frequency.
            amp1|2 (int/float): Sets the generator's RF output power.
            alcState (int): Turns the ALC (automatic level control) on or off. (1, 0)
            iqScale (int): Scales the IQ modulator. Default/safe value is 70
            refSrc (str): Sets the reference clock source. ('int', 'ext', 'bbg')
            fs (float): Sets the sample rate of the baseband generator.
        """

        # Check to see which keyword arguments the user sent and call the appropriate function
        for key, value in kwargs.items():
            if "2" in key and self.numCh != 2:
                raise KeyError(f'Channel 2 not present in this VXG. Invalid keyword argument: "{key}"')
            elif key == "rfState1" or key == "rfState":
                self.set_rfState(value, ch=1)
            elif key == "rfState2" and self.numCh == 2:
                self.set_rfState(value, ch=2)
            elif key == "modState1" or key == "modState":
                self.set_modState(value, ch=1)
            elif key == "modState2" and self.numCh == 2:
                self.set_modState(value, ch=2)
            elif key == "arbState1" or key == "arbState":
                self.set_arbState(value, ch=1)
            elif key == "arbState2" and self.numCh == 2:
                self.set_modState(value, ch=2)
            elif key == "cf1" or key == "cf":
                self.set_cf(value, ch=1)
            elif key == "cf2" and self.numCh == 2:
                self.set_cf(value, ch=2)
            elif key == "amp1" or key == "amp":
                self.set_amp(value, ch=1)
            elif key == "amp2" and self.numCh == 2:
                self.set_amp(value, ch=2)
            elif key == "alcState1" or key == "alcState":
                self.set_alcState(value, ch=1)
            elif key == "alcState2" and self.numCh == 2:
                self.set_alcState(value, ch=2)
            elif key == "iqScale1" or key == "iqScale":
                self.set_iqScale(value, ch=1)
            elif key == "iqScale2" and self.numCh == 2:
                self.set_iqScale(value, ch=2)
            elif key == "rms1" or key == "rms":
                self.set_rms(value, ch=1)
            elif key == "rms2" and self.numCh == 2:
                self.set_rms(value, ch=2)
            elif key == "fs1" or key == "fs":
                self.set_fs(value, ch=1)
            elif key == "fs2" and self.numCh == 2:
                self.set_fs(value, ch=2)
            elif key == "refSrc":
                self.set_refSrc(value)
            else:
                raise KeyError(f'Invalid keyword argument: "{key}"')  # raise KeyError('Invalid keyword argument.')

        # Arb state can only be turned on after a waveform has been loaded/selected
        # self.write(f'radio:arb:state {arbState}')
        # self.arbState = self.query('radio:arb:state?').strip()

        self.err_check()

    def channel_checker(self, ch):
        """
        Helper function to check how many channels the VXG has.
        Args:
            ch (int): Channel number
        """
        
        if ch not in [1, 2]:
            raise ValueError("Invalid channel selected. Choose 1 or 2.")
        if ch == 2 and self.numCh != 2:
            raise ValueError("You have selected channel 2. This is a single channel VXG. Try channel 1 instead.")

    def set_rfState(self, rfState, ch=1):
        """
        Sets and reads the state of the RF output using SCPI commands.
        Args:
            rfState (int): Turns the RF output on or off. (1, 0)
            ch (int): Specified channel being adjusted.
        """

        self.channel_checker(ch)
        if rfState not in [1, 0, "on", "off", "ON", "OFF", "On", "Off"]:
            raise ValueError('"rfState" should be 1, 0, "on", or "off"')

        self.write(f"source:rf{ch}:output:state {rfState}")
        exec(f'self.rfState{ch} = int(self.query(f"source:rf{ch}:output:state?").strip())')

    def set_modState(self, modState, ch=1):
        """
        Sets and reads the state of the internal baseband modulator output using SCPI commands.
        Args:
            modState (int): Turns the baseband modulator on or off. (1, 0)
            ch (int): Specified channel being adjusted.
        """

        self.channel_checker(ch)
        if modState not in [1, 0, "on", "off", "ON", "OFF", "On", "Off"]:
            raise ValueError('"modState" should be 1, 0, "on", or "off"')

        self.write(f"source:rf{ch}:output:modulation {modState}")
        exec(f'self.modState{ch} = int(self.query(f"source:rf{ch}:output:modulation?").strip())')

    def set_arbState(self, arbState, ch=1):
        """
        Sets and reads the state of the internal arb waveform generator using SCPI commands.
        Args:
            arbState (int): Turns the arb waveform generator on or off. (1, 0)
            ch (int): Specified channel being adjusted.
        """

        self.channel_checker(ch)
        if arbState not in [1, 0, "on", "off", "ON", "OFF", "On", "Off"]:
            raise ValueError('"arbState" should be 1, 0, "on", or "off"')

        self.write(f"source:signal{ch}:state {arbState}")
        exec(f'self.arbState{ch} = int(self.query(f"source:signal{ch}:state?").strip())')

    def set_cf(self, cf, ch=1):
        """
        Sets and reads the center frequency of the signal generator output using SCPI commands.
        Args:
            cf (float): Sets the generator's carrier frequency.
            ch (int): Specified channel being adjusted.
        """

        self.channel_checker(ch)

        # Type checking with a useful error message
        try:
            float(cf)
        except ValueError:
            raise ValueError("Carrier frequency must be a positive floating point value.")
        if cf <= 0:
            raise ValueError("Carrier frequency must be a positive floating point value.")

        self.write(f"source:rf{ch}:frequency {cf}")
        exec(f'self.cf = float(self.query(f"source:rf{ch}:frequency?").strip())')

    def set_amp(self, amp, ch=1):
        """
        Sets and reads the output amplitude of signal generator output using SCPI commands.
        Args:
            amp (int/float): Sets the generator's RF output power.
            ch (int): Specified channel being adjusted.
        """

        self.channel_checker(ch)

        # Type checking with a useful error message
        try:
            float(amp)
            int(amp)
        except ValueError:
            raise ValueError('"amp" should be a numerical value.')

        self.write(f"source:rf{ch}:power {amp}")
        exec(f'self.amp{ch} = float(self.query(f"source:rf{ch}:power?").strip())')

    def set_alcState(self, alcState, ch=1):
        """
        Sets and reads the state of the ALC (automatic level control) output using SCPI commands.
        This should be turned off for narrow pulses and signals with rapid amplitude changes.
        Args:
            alcState (int): Turns the ALC (automatic level control) on or off. (1, 0)
            ch (int): Specified channel being adjusted.
        """

        self.channel_checker(ch)
        if alcState not in [1, 0, "on", "off", "ON", "OFF", "On", "Off"]:
            raise ValueError('"alcState" should be 1, 0, "on", or "off"')

        self.write(f"source:rf{ch}:power:alc {alcState}")
        exec(f'self.alcState{ch} = int(self.query(f"source:rf{ch}:power:alc?").strip())')

    def set_iqScale(self, iqScale, ch=1):
        """
        Sets and reads the scaling of the baseband IQ waveform output using SCPI commands.
        Should be about 70 percent to avoid clipping.
        Args:
            iqScale (int): Scales the IQ modulator in percent. Default/safe value is 70, range is 0 to 100.
            ch (int): Specified channel being adjusted.
        """

        self.channel_checker(ch)

        # Type checking with a useful error message
        try:
            int(iqScale)
        except ValueError:
            raise ValueError("iqScale argument must be an integer between 1 and 100.")
        if iqScale <= 0 or iqScale > 100:
            raise ValueError("iqScale argument must be an integer between 1 and 100.")

        self.write(f"source:signal{ch}:waveform:scale {iqScale}")
        exec(f'self.iqScale{ch} = float(self.query(f"source:signal{ch}:waveform:scale?").strip())')

    def set_rms(self, rms, ch=1):
        """
        Sets and reads the RMS value of the baseband IQ waveform output using SCPI commands.
        Should be set to 1 for combined pulsed signals.
        Args:
            rms (float): Waveform RMS power calculation. VXG will offset RF power to ensure measured RMS power matches the user-specified RF power.
            ch (int): Specified channel being adjusted.
        """

        self.channel_checker(ch)
        
        # Type checking with a useful error message
        try:
            int(rms)
            float(rms)
        except ValueError:
            raise ValueError('"rms" must be a floating point value between 0.1 and 1.414213562.')
        if rms <= 0.1 or rms > 1.414213562:
            raise ValueError('"rms" must be a floating point value between 0.1 and 1.414213562.')

        self.write(f"source:signal{ch}:waveform:rms {rms}")
        exec(f'self.rms{ch} = float(self.query(f"source:signal{ch}:waveform:rms?").strip())')

    def set_fs(self, fs, ch=1):
        """
        Sets and reads sample  rate of internal arb using SCPI commands.
        Args:
            fs (float): Sample rate.
            ch (int): Specified channel being adjusted.
        """

        self.channel_checker(ch)

        # Type checking with a useful error message
        try:
            int(fs)
            float(fs)
        except ValueError:
            raise ValueError("Sample rate must be a positive floating point value.")
        if fs <= 0:
            raise ValueError("Sample rate must be a positive floating point value.")

        self.write(f"signal{ch}:waveform:sclock:rate {fs}")
        exec(f"self.fs{ch} = float(self.query('signal{ch}:waveform:sclock:rate?').strip())")

    def set_refSrc(self, refSrc):
        """
        Sets and reads the reference clock source output using SCPI commands.
        Args:
            refSrc (str): Sets the reference clock source. ('int', 'ext', 'bbg')
        """

        if not isinstance(refSrc, str) or refSrc.lower() not in ["int", "ext", "internal", "external"]:
            raise ValueError('"refSrc" must be "internal" or "external".')

        self.write(f"roscillator:source {refSrc}")
        self.refSrc = self.query("roscillator:source?").strip()
        if "int" in self.refSrc.lower():
            self.refFreq = 10e6
        elif "ext" in self.refSrc.lower():
            self.refFreq = float(self.query("roscillator:frequency:external?").strip())
        elif "bbg" in self.refSrc.lower():
            self.refFreq = float(self.query("roscillator:frequency:bbg?").strip())
        else:
            raise error.InstrumentError("Unknown refSrc selected.")

    def sanity_check(self):
        """Prints out initialized values."""
        print("RF State 1:", self.rfState1)
        print("Modulation State 1:", self.modState1)
        print("Center Frequency 1:", self.cf1)
        print("Output Amplitude 1:", self.amp1)
        print("ALC state 1:", self.alcState1)
        print("IQ Scaling 1:", self.iqScale1)
        print("RMS 1:", self.rms1)
        print("Reference Source:", self.refSrc)
        print("Internal Arb1 State:", self.arbState1)
        print("Internal Arb1 Sample Rate:", self.fs1)

        if self.numCh == 2:
            print("\nRF State 2:", self.rfState2)
            print("Modulation State 2:", self.modState2)
            print("Center Frequency 2:", self.cf2)
            print("Output Amplitude 2:", self.amp2)
            print("ALC state 2:", self.alcState2)
            print("IQ Scaling 2:", self.iqScale2)
            print("RMS 2:", self.rms2)
            print("Internal Arb2 State:", self.arbState2)
            print("Internal Arb2 Sample Rate:", self.fs2)

    def download_wfm(self, wfmData, wfmID="wfm", sim=False):
        """
        Defines and downloads a waveform into the waveform memory.
        Returns useful waveform identifier.
        Args:
            wfmData (NumPy array): Complex waveform values.
            wfmID (str): Waveform name.

        Returns:
            (str): Useful waveform identifier/name. Use this as the waveform identifier for the .play() method.
        """

        # Stop output before doing anything else
        self.write("radio:arb:state off")
        self.write("rf1:output:modulation off")
        self.arbState = self.query("radio:arb:state?").strip()

        # Waveform format checking. VXG can only use 'iq' format waveforms.
        if not isinstance(wfmData, np.ndarray):
            raise TypeError("wfmData should be a complex NumPy array.")

        if wfmData.dtype != complex:
            raise TypeError("Invalid wfm type. IQ waveforms must be an array of complex values.")
        else:
            i = self.check_wfm(np.real(wfmData))
            q = self.check_wfm(np.imag(wfmData))

            wfm = self.iq_wfm_combiner(i, q)

        # try:
        #     self.write(f'mmemory:delete "D:\\Users\\Instrument\\Documents\\Keysight\\PathWave\\SignalGenerator\\Waveforms\\{wfmID}.bin"')
        #     self.query('*opc?')
        #     self.err_check()
        # except socketscpi.SockInstError:
        #     print('Waveform doesn\'t exist, skipping delete operation.')
        # pass

        # self.write(f'source:signal:waveform:select "D:\\Users\\Instrument\\Documents\\Keysight\\PathWave\\SignalGenerator\\Waveforms\\{wfmID}.bin"')
        
        # self.write_binary_values(
        #     f'mmemory:data "D:\\Users\\Instrument\\Documents\\Keysight\\PathWave\\SignalGenerator\\Waveforms\\{wfmID}.bin",',
        #     wfm,
        # )

        # Save waveform to specified location on hard drive.
        if sim:
            self.write_binary_values(f'mmemory:data "C:\\Temp\\{wfmID}.bin",', wfm, datatype='h')
        else:
            self.write_binary_values(f'mmemory:data "D:\\Users\\Instrument\\Documents\\Keysight\\PathWave\\SignalGenerator\\Waveforms\\{wfmID}.bin",', wfm, datatype='h')
            
        return wfmID

    @staticmethod
    def iq_wfm_combiner(i, q):
        """
        Combines i and q wfms into a single interleaved wfm for download to generator.
        Args:
            i (NumPy array): Array of real waveform samples.
            q (NumPy array): Array of imaginary waveform samples.

        Returns:
            (NumPy array): Array of interleaved IQ values.
        """

        iq = np.empty(2 * len(i), dtype=np.int16)
        iq[0::2] = i
        iq[1::2] = q
        return iq

    def check_wfm(self, wfm):
        """
        HELPER FUNCTION
        Checks minimum size and granularity and returns waveform with
        appropriate binary formatting. Note that sig gens expect big endian
        byte order.

        See pages 205-256 in Keysight X-Series Signal Generators Programming
        Guide (November 2014 Edition) for more info.
        Args:
            wfm (NumPy array): Unscaled/unformatted waveform data.

        Returns:
            (NumPy array): Waveform data that has been scaled and
                formatted appropriately for download to AWG
        """

        # If waveform length doesn't meet granularity or minimum length requirements, repeat the waveform until it does
        repeats = wraparound_calc(len(wfm), self.gran, self.minLen)
        wfm = np.tile(wfm, repeats)
        rl = len(wfm)
        if rl < self.minLen:
            raise error.InstrumentError(f"Waveform length: {rl}, must be at least {self.minLen}.")
        if rl % self.gran != 0:
            raise error.GranularityError(f"Waveform must have a granularity of {self.gran}.")

        return np.array(self.binMult * wfm, dtype=np.int16).byteswap()

    def delete_wfm(self, wfmID):
        """
        Stops output and deletes specified waveform.
        Args:
            wfmID (str): Name of waveform to be deleted.
        """

        self.stop()
        if "M938" in self.instId:
            self.write(f'memory:delete "{wfmID}"')
        else:
            self.write(f'memory:delete "WFM1:{wfmID}"')
        self.err_check()

    def clear_all_wfm(self):
        """Stops output and deletes all iq waveforms."""
        self.stop()
        self.write("mmemory:delete:wfm")
        self.err_check()

    def play(self, wfmID="wfm", ch=1, sim=False, *args, **kwargs):
        """
        Selects waveform and activates arb mode, RF output, and modulation.
        Args:
            wfmID (str): Waveform identifier, used to select waveform to be played.
            ch (int): Specified channel being adjusted.
        **kwargs:
            rms (float): Waveform RMS power calculation. VXG will offset RF power to ensure measured RMS power matches the user-specified RF power.
        """

        if ch not in [1, 2]:
            raise ValueError("Invalid channel selected. Choose 1 or 2.")
        if ch == 2 and self.numCh != 2:
            raise ValueError("You have selected channel 2. This is a single channel VXG. Try channel 1 instead.")
        
        # Load waveform from specified location on hard drive
        if sim:
            self.write(f'source:signal{ch}:waveform:select "C:\\Temp\\{wfmID}.bin"')
        else:
            self.write(f'source:signal{ch}:waveform:select "D:\\Users\\Instrument\\Documents\\Keysight\\PathWave\\SignalGenerator\\Waveforms\\{wfmID}.bin"')

        # Turn on arb, RF output and modulation
        self.set_arbState(1, ch)
        self.set_rfState(1, ch)
        self.set_modState(1, ch)

        # Don't know why, but the VXG uses a weird sample rate number when the waveform is selected, so we use the one we set in .configure()
        exec(f"self.set_fs(self.fs{ch}, {ch})")

        # The RMS value set by .configure() is overwritten by the VXG's internal calculation when waveform is selected, so we will apply the one we set in .configure() if the 'rms' keyword arg is present.
        for key, value in kwargs.items():
            if key == "rms":
                self.set_rms(value, ch=ch)

        self.err_check()

    def stop(self, ch=1):
        """
        Dectivates arb mode, RF output, and modulation per channel.
        Args:
            ch (int): Channel on which to stop playback.
        """

        if ch not in [1, 2]:
            raise ValueError("Invalid channel selected. Choose 1 or 2.")
        if ch == 2 and self.numCh != 2:
            raise ValueError("You have selected channel 2. This is a single channel VXG. Try channel 1 instead.")

        self.set_arbState(0, ch=ch)
        self.set_rfState(0, ch=ch)
        self.set_modState(0, ch=ch)


class   N5186A(VXG):
    def __init__(self, ipAddress, apiType="socketscpi", timeout=10, reset=False, **kwargs):
        """
        Generic class for controlling the N5186A Vector MXG signal generator.

        Attributes:
            rf1State (int): Turns the RF output on or off. (1, 0)
            modState (int): Turns the baseband modulator on or off. (1, 0)
            cf (float): Sets the generator's carrier frequency.
            amp (int/float): Sets the generator's RF output power.
            alcState (int): Turns the ALC (automatic level control) on or off. (1, 0)
            iqScale (int): Scales the IQ modulator. Default/safe value is 70
            refSrc (str): Sets the reference clock source. ('int', 'ext', 'bbg')
            fs (float): Sets the sample rate of the baseband generator.

        TODO
            Add check to ensure that the correct instrument is connected
        """

        # super().__init__(host, port, timeout)
        super().__init__(ipAddress, apiType=apiType, timeout=timeout, **kwargs)
        if reset:
            self.write("*rst")
            self.query("*opc?")
        
        # Set the byte order to big endian
        self.write(':SYSTem:WAVeform:BFILe:FORMat:DEFault I16Big')

        # query the options on the MXG to see how many channels it has
        self.numCh = 0
        for ch in range(1,5):
            optionString = self.query(f'system:rf{ch}:opt?').strip()
            if optionString != '""':
                self.numCh += 1
        print(f'Number of channels: {self.numCh}')

        for ch in range(1, self.numCh + 1):
            print(ch)
            exec(f'self.rfState{ch} = self.query("rf{ch}:output?").strip()')
            exec(f'self.modState{ch} = self.query("rf{ch}:output:modulation?").strip()')
            exec(f'self.cf{ch} = float(self.query("source:rf{ch}:frequency?").strip())')
            exec(f'self.amp{ch} = float(self.query("rf{ch}:power?").strip())')
            exec(f'self.arbState{ch} = self.query("source:group{ch}:signal:state?").strip()')
            exec(f'self.alcState{ch} = self.query("rf{ch}:power:alc?")')
            exec(f'self.iqScale{ch} = float(self.query("source:group{ch}:signal:waveform:scale?").strip())')
            exec(f'self.rms{ch} = float(self.query("source:group{ch}:signal:waveform:rms?").strip())')
            exec(f'self.fs{ch} = float(self.query("source:group{ch}:signal:waveform:sclock:rate?").strip())')
        
    def delete_wfm(self, wfmID):
        """
        Stops output and deletes specified waveform.
        Args:
            wfmID (str): Name of waveform to be deleted.
        """

        self.stop()
        if "M938" in self.instId:
            self.write(f'memory:delete "{wfmID}"')
        else:
            self.write(f'memory:delete "WFM1:{wfmID}"')
        self.err_check()

    def clear_all_wfm(self):
        """Stops output and deletes all iq waveforms."""
        self.stop()
        self.write("mmemory:delete:wfm")
        self.err_check()
