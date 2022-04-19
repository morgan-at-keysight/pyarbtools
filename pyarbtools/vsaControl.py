"""
vsaControl
Author: Morgan Allison, Keysight RF/uW Application Engineer
Generic VSA control object for PyArbTools.
"""

from ctypes import ArgumentError
from multiprocessing.sharedctypes import Value
from weakref import KeyedRef
import socketscpi
import os
import warnings
import numpy as np
from pyarbtools import error


class VSA(socketscpi.SocketInstrument):
    """
    Generic class for controlling Keysight 89600 Vector Signal Analysis Software

    Attributes:
        cf (float): Analyzer center frequency in Hz
        amp (float): Reference level/vertical range in dBm
        span (float): Analyzer span in Hz
        hw (str): Identifier string for acquisition hardware used by VSA
        meas (str): Measurement type ('vector', 'ddemod' currently supported)

        modType (str): String defining digital modulation format. This is CASE-SENSITIVE and must be surrounded by double quotes.
        symRate (float): Symbol rate in symbols/sec.
        measFilter (str): Sets the measurement filter type. This is CASE-SENSITIVE and must be surrounded by double quotes.
        refFilter (str): Sets the reference filter type. This is CASE-SENSITIVE and must be surrounded by double quotes.
        filterAlpha (float): Filter alpha/rolloff factor. Must  be between 0 and 1.
        measLength (int): Measurement length in symbols.
        eqState (bool): Turns the equalizer on or off.
        eqLength (int): Length of the equalizer filter in symbols.
        eqConvergence (float): Equalizer convergence factor.

        rbw (float): Resolution bandwidth in Hz.
        time (float): Analysis time in sec.
    """

    def __init__(self, host, port=5025, timeout=10, reset=False, vsaHardware=None):
        super().__init__(host, port, timeout)

        # Set up hardware
        if not isinstance(vsaHardware, str) and vsaHardware is not None:
            raise error.VSAError('vsaHardware must be a string indicating which hardware platform to use.')

        self.hw = vsaHardware
        if vsaHardware is not None:
            self.set_hw(vsaHardware)

        if reset:
            # Reset, wait for reset to finish, and stop acquisition
            self.write('system:preset')
            self.query('*opc?')
            self.write('init:pause')

        # Pause measurement before doing anything
        self.write('init:pause')

        # Initialize global attributes
        self.cf = float(self.query('sense:frequency:center?'))
        self.amp = float(self.query('input:analog:range:dbm?'))
        self.span = float(self.query('sense:frequency:span?'))
        self.meas = self.query('measure:configure?')
        self.dataSource = self.query('input:data:feed?')

        # Initialize measurement-specific attributes.
        # Digital Demod
        self.modType = ''
        self.symRate = 0
        self.measFilter = ''
        self.refFilter = ''
        self.filterAlpha = 0
        self.measLength = 0
        self.eqState = False
        self.eqLength = 0
        self.eqConvergence = 0

        # Vector
        self.rbw = 0
        self.time = 0

    def acquire_continuous(self):
        """Begins continuous acquisition in VSA using SCPI commands."""
        self.write('initiate:continuous on')
        self.write('initiate:immediate')

    def acquire_single(self):
        """Sets single acquisition mode and takes a single acquisition in VSA using SCPI commands."""
        self.write('initiate:continuous off')
        self.write('initiate:immediate')
        self.query('*opc?')

    def stop(self):
        """Stops acquisition in VSA using SCPI commands."""
        self.write('initiate:pause')

    def autorange(self):
        """Executes an amplitude autorange in VSA and waits for it to complete using SCPI commands."""

        # Gotta make sure measurement is running while doing this
        self.write('initiate:continuous on')
        self.write('initiate:immediate')

        self.write('input:analog:range:auto')
        self.query('*opc?')

        # Turn it back off when we're done
        self.write('initiate:continuous off')

    def evm_opt(self, timeout):
        """Executes an amplitude autorange using EVM optimization criteria.
        
        Args:
            timeout (int): Temporary timeout in seconds.
        """

        if not isinstance(timeout, (int, float)) or timeout < 0:
            raise TypeError('"timeout" must be positive integer.')

        # Gotta make sure measurement is running while doing this
        self.write('initiate:continuous on')
        self.write('initiate:immediate')

        # Save the original timeout so it can be reset after the optimization
        originalTimeout = self.socket.timeout
        
        self.socket.settimeout(timeout)
        self.write(f"input:analog:criteria:range:auto 'EvmAlgorithm', {timeout*1000}")
        self.query('*opc?')
        
        self.socket.settimeout(originalTimeout)

        # Turn it back off when we're done
        self.write('initiate:continuous off')

    def set_hw(self, hw):
        """
        Sets and reads hardware configuration for VSA. Checks to see if selected hardware is valid.
        Args:
            hw (str): Identifier string for acquisition hardware used for VSA
        """

        # Get list of available hardware
        hwList = self.query('system:vsa:hardware:configuration:catalog?').split(',')

        # Check to see if user-selected hardware is available
        if f'"{hw}"' not in hwList:
            raise ValueError('Selected hardware not present in VSA hardware list.')

        # If available, connect and wait for operation to finish
        self.write(f'system:vsa:hardware:configuration:select "{hw}"')
        self.query('*opc?')
        self.hw = self.query('system:vsa:hardware:configuration:select?')

    def set_data_source(self, fromHardware=True):
        """
        Sets the data source VSA uses for its IQ data.

        Args:
            fromHardware (bool): True uses data from hardware, False uses data from a recording.
        """

        if fromHardware:
            self.write("input:data:feed hw")
        else:
            self.write("input:data:feed rec")
        self.dataSource = self.query("input:data:feed?")

    def recall_setup(self, setupFile):
        """
        Loads a .setx file to set up VSA.

        Args:
            setupFile (str): Absolute path to a .setx file.
        """
        # if not os.path.exists(setupFile):
            # raise error.VSAError('Path or file name does not exist.')
        
        self.write(f'mmemory:load:setup "{setupFile}"')

        # VSA helpfully reports an error if the file and the selected file format don't match. Check this here.
        self.err_check()

    def recall_recording(self, fileName, fileFormat='csv'):
        """
        Recalls a data file as a recording in VSA using SCPI commands.
        Args:
            fileName (str): Full absolute file name of the recording to be loaded.
            fileFormat (str): Format of recording file. ('CSV', 'E3238S', 'MAT', 'MAT7', 'N5110A', 'N5106A', 'SDF', 'TEXT')
        """

        # if not os.path.exists(fileName):
        #     raise error.VSAError('Path or file name does not exist.')

        # Ensure fileName is a valid file type
        validExtensions = ['csv', 'cap', 'mat', 'hdf', 'h5', 'bin', 'sdf', 'dat', 'txt']
        if fileName.split('.')[-1].lower() not in validExtensions:
            raise error.VSAError(f'Invalid file format. Extension must be in {validExtensions}')

        # Ensure fileFormat is a valid choice
        if fileFormat.lower() not in ['csv', 'e3238s', 'mat', 'mat7', 'n5110a', 'n5106a', 'sdf', 'text']:
            raise error.VSAError('Incorrect file format. Must be "csv", "e3238s", "mat", "mat7", "n5110a", "n5106a", "sdf", or "text".')

        # Load the recording
        self.write(f'mmemory:load:recording "{fileName}", "{fileFormat}"')

        # VSA helpfully reports an error if the file and the selected file format don't match. Check this here.
        self.err_check()

    def get_iq(self, newAcquisition=False):
        """
        Gets IQ data using current acquisition settings.
        
        Args:
            newAcquisition (bool): Determines if a new acquisition is made prior to getting IQ data.

        Returns:
            (NumPy ndarray): Array of complex IQ values
        """

        # if 'vect' not in self.meas.lower():
            # raise error.VSAError(f'Measurement type is currently "{self.meas}". Measurement type must be "vect" to capture IQ data.')

        # Get the measurement to determine the correct data to use for the IQ trace
        self.get_measurement()

        if newAcquisition:
            self.acquire_single()

        # Add new trace in IQ format
        iqTraceNum = int(self.query("trace:count?")) + 1
        self.write("trace:add")

        # For whatever reason, the name of the time trace is different in different measurement modes.
        if 'vect' in self.meas.lower():
            self.write(f"trace{iqTraceNum}:data:name 'Main Time1'")
        elif 'cust' in self.meas.lower() or 'ddem' in self.meas.lower():
            self.write(f"trace{iqTraceNum}:data:name 'Time1'")
        else:
            raise AttributeError("Invalid 'meas' value.")
        self.write(f"trace{iqTraceNum}:format 'IQ'")

        # Format the trace and grab trace data
        self.write('format:trace:data real64')
        i = self.binblockread(f'trace{iqTraceNum}:data:x?', datatype='d').byteswap()
        q = self.binblockread(f'trace{iqTraceNum}:data:y?', datatype='d').byteswap()
        
        # Convert individual I and Q arrays into complex array
        iq = np.array(i + 1j*q)

        # Clean up trace used for acquisition
        self.write("trace:remove")

        self.err_check()

        return iq

    def set_cf(self, cf):
        """
        Sets and reads center frequency for VSA using SCPI commands.

        Args:
            cf (float): Analyzer center frequency in Hz.
        """

        if not isinstance(cf, float) or cf <= 0:
            raise ValueError('Center frequency must be a positive floating point value.')

        self.write(f'sense:frequency:center {cf}')
        self.cf = float(self.query('sense:frequency:center?'))

    def set_amp(self, amp):
        """
        Sets and reads reference level/vertical range for VSA using SCPI commands.

        Args:
            amp (float): Analyzer reference level/vertical range in dBm.
        """

        if not isinstance(amp, float) and not isinstance(amp, int):
            raise ValueError('Reference level/vertical range must be a numerical value.')

        self.write(f'input:analog:range:dbm {amp}')
        self.amp = float(self.query('input:analog:range:dbm?'))

    def set_span(self, span):
        """
        Sets and reads span for VSA using SCPI commands

        Args:
            span (float): Frequency span in Hz.
        """

        if not isinstance(span, float) and not isinstance(span, int):
            raise ValueError('Span must be a positive numerical value.')

        self.write(f'sense:frequency:span {span}')
        self.span = float(self.query('sense:frequency:span?'))

    def set_attenuation(self, atten):
        """
        Sets mechanical attenuator.

        Args:
            atten (int): Attenuator value in dB.
        """

        if not isinstance(atten, float) and not isinstance(atten, int):
            raise ValueError('"atten" must be a positive numerical value.')

        # Set range control method to "attenuation"
        self.write('input:extension:parameters:set "RangeInformationRangeControl", 1')
        
        # Set mechanical attenuator value
        self.write(f'input:extension:parameters:set "RangeInformationMechAtten", {atten}')
        self.err_check()

    def set_if_gain(self, ifGain):
        """
        Sets IF Gain value.

        Args:
            ifGain (int): IF Gain value in dB (range from -32 to +32).
        """

        if not isinstance(ifGain, float) and not isinstance(ifGain, int):
            raise ValueError('"ifGain" must be a numerical value.')

        # Set range control method to "attenuation"
        self.write('input:extension:parameters:set "RangeInformationRangeControl", 1')
        
        # Set IF Gain value
        self.write(f'input:extension:parameters:set "RangeInformationIFGain", {ifGain}')
        self.err_check()
    
    def set_amplifier(self, amplifier):
        """
        Sets IF Gain value.

        Args:
            amplifier (int): Amplifier setting (0=none, 1=preamp, 2=LNA, 3=LNA+preamp).
        """

        if amplifier not in [0, 1, 2, 3]:
            raise ValueError('"amplifier" must be 0 (none), 1 (preamp), 2 (LNA), or 3 (LNA+preamp).')

        # Set range control method to "attenuation"
        self.write('input:extension:parameters:set "RangeInformationRangeControl", 1')
        
        # Set IF Gain value
        self.write(f'input:extension:parameters:set "RangeInformationPreamplifier", {amplifier}')
        self.err_check()

    def set_measurement(self, meas):
        """
        Selects a measurement type in VSA using SCPI commands.

        Args:
            meas (str): Selects measurement type ('vector', 'ddemod' currently supported, limited support for Custom OFDM)
        """

        if meas.lower() not in ['vector', 'vect', 'ddemod', 'ddem', 'customofdm', 'cust']:
            raise ValueError("Invalid measurement selected. Choose 'vector', 'ddemod', or 'customofdm.")

        self.write('measure:nselect 1')
        self.write(f'measure:configure {meas}')
        self.get_measurement()

        if 'vect' in self.meas.lower():
            self.write('sense:rbw:points:auto 1')

    def get_measurement(self):
        """
        Queries and populates the self.meas property with the currently selected measurement type.
        """

        self.meas = self.query('measure:configure?')

    def configure_ddemod(self, **kwargs):
        """
        Configures digital demodulation settings in VSA using SCPI commands.
        Keyword Args:
            cf (float): Analyzer center frequency in Hz.
            amp (float): Analyzer reference level/vertical range in dBm.
            modType (str): String defining digital modulation format.
            symRate (float): Symbol rate in symbols/sec.
            measFilter (str): Sets the measurement filter type.
            refFilter (str): Sets the reference filter type.
            filterAlpha (float): Filter alpha/rolloff factor. Must  be between 0 and 1.
            measLength (int): Measurement length in symbols.
            eqState (bool): Turns the equalizer on or off.
            eqLength (int): Length of the equalizer filter in symbols.
            eqConvergence (float): Equalizer convergence factor.
        """

        if 'ddem' not in self.meas.lower():
            raise error.VSAError(f'Measurement type is currently "{self.meas}". Measurement type must be "ddem" to configure digital demod.')

        # Check to see which keyword arguments the user sent and call the appropriate function
        for key, value in kwargs.items():
            if key == 'cf':
                self.set_cf(value)
            elif key == 'amp':
                self.set_amp(value)
            elif key == 'span':
                self.set_span(value)
            elif key == 'modType':
                self.set_modType(value)
            elif key == 'symRate':
                self.set_symRate(value)
            elif key == 'measFilter':
                self.set_measFilter(value)
            elif key == 'refFilter':
                self.set_refFilter(value)
            elif key == 'filterAlpha':
                self.set_filterAlpha(value)
            elif key == 'measLength':
                self.set_measLength(value)
            elif key == 'eqState':
                self.set_eqState(value)
            elif key == 'eqLength':
                self.set_eqLength(value)
            elif key == 'eqConvergence':
                self.set_eqConvergence(value)
            else:
                raise KeyError(f'Invalid keyword argument: "{key}"')

            # Handy way to actually visualize everything. The defaults in VSA are terrible.
            self.write('display:layout 2, 2')

        self.err_check()

    def set_modType(self, modType):
        """
        Sets and reads modulation format in VSA digital demod using SCPI commands.
        Args:
            modType (str): String defining modulation format.
        """

        if modType.lower() not in ['qam16', 'qam32', 'qam64', 'qam256', 'qpsk', 'differentialqpsk', 'pi4differentialqpsk', 'offsetqpsk', 'bpsk', 'psk8', 'msk', 'msk2', 'fsk2', 'fsk4', 'dvbqam16', 'dvbqam32', 'dvbqam64', 'vsb8', 'vsb16', 'edge', 'fsk8', 'fsk16', 'qam128', 'differentialpsk8', 'qam512', 'qam1024', 'apsk16', 'apsk16dvb', 'apsk32', 'apsk32dvb', 'dvbqam128', 'dvbqam256', 'pi8differentialpsk8', 'cpmfm', 'star16qam', 'star32qam', 'customapsk', 'shapedoffsetqpsk', 'qam2048', 'qam4096']:
            raise ValueError('Invalid modulation type chosen.')

        self.write(f'ddemod:mod "{modType}"')
        self.modType = self.query('ddemod:mod?').lower()

    def set_symRate(self, symRate):
        """
        Sets and reads symbol rate in VSA digital demod using SCPI commands.
        Args:
            symRate (float): Symbol rate in symbols/sec.
        """

        if not isinstance(symRate, float) and not isinstance(symRate, int) or symRate < 0:
            raise ValueError('Symbol rate must be a positive floating point value.')

        self.write(f'ddemod:srate {symRate}')
        self.symRate = float(self.query('ddemod:srate?'))

    def set_measFilter(self, measFilter):
        """
        Sets and reads measurement filter type in VSA digital demod using SCPI commands.
        Args:
            measFilter (str): Sets the measurement filter type.
        """

        if measFilter.lower() not in ['none', 'rectangular', 'rootraisedcosine', 'gaussian', 'userdefined', 'lowpass', 'is95basephasecompensating', 'edge']:
            raise ValueError(f'Invalid measurement filter selected: {measFilter}')

        self.write(f'ddemod:filter "{measFilter}"')
        self.measFilter = self.query('ddemod:filter?')

    def set_refFilter(self, refFilter):
        """
        Sets and reads measurement filter type in VSA digital demod using SCPI commands.
        Args:
            refFilter (str): Sets the reference filter type.
        """

        if refFilter.lower() not in ['rectangular', 'raisedcosine', 'rootraisedcosine', 'gaussian', 'userdefined', 'is95baseband', 'edge', 'halfsine', 'rectangularonesymbolduration', 'raisedcosinethreesymbolduration', 'shapedoffsetqpsktgirig10604', 'raisedcosinefoursymbolduration', 'shapedoffsetqpska', 'shapedoffsetqpskb']:
            raise ValueError('Invalid reference filter selected.')

        self.write(f'ddemod:filter:reference "{refFilter}"')
        self.refFilter = self.query('ddemod:filter:reference?')

    def set_filterAlpha(self, filterAlpha):
        """
        Sets and reads filter alpha/rolloff factor in VSA digital demod using SCPI commands.
        Args:
            filterAlpha (float): Filter alpha/rolloff factor. Must  be between 0 and 1.
        """

        if not isinstance(filterAlpha, float) or filterAlpha < 0 or filterAlpha > 1:
            raise ValueError('filterAlpha must be a floating point value between 0 and 1')

        self.write(f'ddemod:filter:abt {filterAlpha}')
        self.filterAlpha = float(self.query('ddemod:filter:abt?'))

    def set_measLength(self, measLength):
        """
        Sets and reads measurment length in VSA digital demod using SCPI commands.
        Args:
            measLength (int): Measurement length in symbols.
        """

        if not isinstance(measLength, int) or measLength < 10 or measLength > 4096:
            raise ValueError('measLength must be a positive integer value between 10 and 4096')

        self.write(f'ddemod:rlength {measLength}')
        self.measLength = int(self.query('ddemod:rlength?'))

    def set_eqState(self, eqState):
        """
        Sets and reads the state of the equalizer in VSA digital demod using SCPI commands.
        Args:
            eqState (bool): Turns the equalizer on or off.
        """

        if not isinstance(eqState, bool):
            raise ValueError('eqState must be True or False.')

        if eqState:
            eqStateArg = 1
        else:
            eqStateArg = 0

        self.write(f'ddemod:compensate:equalize {eqStateArg}')
        ret = self.query('ddemod:compensate:equalize?')

        if ret == '1':
            self.eqState = True
        elif ret == '0':
            self.eqState = False

    def set_eqLength(self, eqLength):
        """
        Sets and reads the equalizer length in symbols in VSA digital demod using SCPI commands.
        Args:
            eqLength (int): Length of the equalizer filter in symbols.
        """

        if not isinstance(eqLength, int) or eqLength < 3 or eqLength > 99:
            raise ValueError('eqLength must be an integer between 3 and 99.')

        self.write(f'ddemod:compensate:equalize:length {eqLength}')
        self.eqLength = int(self.query('ddemod:compensate:equalize:length?'))

    def set_eqConvergence(self, eqConvergence):
        """
        Sets and reads the equalizer convergence factor in VSA digital demod using SCPI commands.
        Args:
            eqConvergence (float): Equalizer convergence factor.
        """

        if not isinstance(eqConvergence, float) or eqConvergence > 1.0:
            raise ValueError('eqConvergence must be a floating point value between about 1e-12 and 1.0')

        self.write(f'ddemod:compensate:equalize:convergence {eqConvergence}')
        self.eqConvergence = float(self.query('ddemod:compensate:equalize:convergence?'))

    def configure_vector(self, **kwargs):
        """
        Configures vector measurement mode in VSA using SCPI commands.

        Keyword Args:
            cf (float): Analyzer center frequency in Hz.
            amp (float): Analyzer reference level/vertical range in dBm.
            span (float): Analyzer span in Hz.
            rbw (float): Resolution bandwidth in Hz.
            time (float): Analysis time in sec.
        """

        if 'vect' not in self.meas.lower():
            raise error.VSAError(f'Measurement type is currently "{self.meas}". Measurement type must be "vect" to configure vector mode.')

        # Check to see which keyword arguments the user sent and call the appropriate function
        for key, value in kwargs.items():
            if key == 'cf':
                self.set_cf(value)
            elif key == 'amp':
                self.set_amp(value)
            elif key == 'span':
                self.set_span(value)
            elif key == 'rbw':
                self.set_rbw(value)
            elif key == 'time':
                self.set_time(value)
            else:
                raise KeyError(f'Invalid keyword argument: "{key}"')

            # Check for conflicting settings in keyword arguments (RBW and acq time).
            lowerKeys = [k.lower() for k in kwargs.keys()]
            if 'time' in lowerKeys and 'rbw' in lowerKeys:
                warnings.warn('When both acquisition time and RBW are set, the last one configured will override the first.')

        self.err_check()

    def set_rbw(self, rbw):
        """
        Sets and reads the resolution bandwidth for VSA vector mode using SCPI commands.

        Args:
            rbw (float): Resolution bandwidth in Hz.
        """

        self.write('sense:rbw:points:auto 1')
        self.write(f'sense:rbw {rbw}')
        self.rbw = float(self.query('sense:rbw?'))
        self.time = float(self.query('sense:time:length?'))

    def set_time(self, time):
        """
        Sets and reads the acquisition time for VSA vector mode using SCPI commands.

        Args:
            time (float): Acquisition time in seconds.
        """

        self.write('sense:rbw:points:auto 1')
        self.write(f'sense:time:length {time}')
        self.time = float(self.query('sense:time:length?'))
        self.rbw = float(self.query('sense:rbw?'))

    def custom_ofdm_format_setup(self, setupFile):
        """Loads a setx file for a Custom OFDM measurement. This **must always be done when setting up 
        a custom OFDM measurement for the first time.
        
        Args:
            setupFile (str): Path to a .setx file that configures the OFDM frame structure and resource mapping.
        """
        self.recall_setup(setupFile)

    def custom_ofdm_time_setup(self, **kwargs):
        """Configures the settings in the Time tab under Custom OFDM demod properties.
        
        Keyword Args:
            measInterval (int): Number of symbols to be included in the measurement.
            measOffset (int): Number of symbols to be omitted prior to beginning the measurement.
            resultLen (int): Number of symbols available for the measurement. 
            resultLenSelect (int): Determines whether to automatically limit the results length to the number of symbols contained in a single burst.
            searchLen (float): Determines total amount of time VSA will acquire for analysis.
        """

        # measInterval=256, measOffset=0, resultLen=256, resultLenAuto=True, searchLen=300e-6
        for key, value in kwargs.items():
            if key == "measInterval":
                self.write(f"sense:customofdm:time:interval {value}")
            elif key == "measOffset":
                self.write(f"sense:customofdm:time:offset {value}")
            elif key == "resultLen":
                self.write(f"sense:customofdm:time:rlength {value}")
            elif key == "resultLenAuto":
                if value:
                    self.write(f"sense:customofdm:time:rlength:selection 'Automatic'")
                else:
                    self.write(f"sense:customofdm:time:rlength:selection 'Manual'")
            elif key == "searchLen":
                self.write(f"sense:customofdm:time:slength {value}")
            else:
                raise KeyError("Invalid keyword argument. Muse be 'measInterval', 'measOffset', 'resultLen', 'resultLenAuto', or 'searchLen'.")

    def custom_ofdm_equalizer_setup(self, **kwargs):
        """Configures the equalizer settings for Custom OFDM.
        
        Args:
            useData (bool): Determines if the equalizer will use Data resource blocks for training.
            useDCPilot (bool): Determines if the equalizer will use DC Pilot for training.
            usePilot (bool): Determines if the equalizer will use Pilot resource blocks for training.
            usePreamble (bool): Determines if the equalizer will use Preamble resource blocks for training.
        """
 
        # useData=False, useDCPilot=False, usePilot=True, usePreamble=True
        for key, value in kwargs.items():
            if key == "useData":
                if value:
                    self.write(f"sense:customofdm:equalizer:data 1")
                else:
                    self.write(f"sense:customofdm:equalizer:data 0")
            elif key == "useDCPilot":
                if value:
                    self.write(f"sense:customofdm:equalizer:dcpilot:enabled 1")
                else:
                    self.write(f"sense:customofdm:equalizer:dcpilot:enabled 0")
            elif key == "usePilot":
                if value:
                    self.write(f"sense:customofdm:equalizer:pilot 1")
                else:
                    self.write(f"sense:customofdm:equalizer:pilot 0")
            elif key == "usePreamble":
                if value:
                    self.write(f"sense:customofdm:equalizer:preamble 1")
                else:
                    self.write(f"sense:customofdm:equalizer:preamble 0")
            else:
                raise KeyError("Invalid keyword argument. Muse be 'useData', 'useDCPilot', 'usePilot', or 'usePreamble'.")

    def custom_ofdm_tracking_setup(self, **kwargs):
        """Configures the tracking settings for Custom OFDM.
        
        Args:
            useData (bool): Determines if tracking includes data subcarriers.
            amplitude (bool): Determines if tracking includes amplitude.
            phase (bool): Determines if tracking includes phase.
            timing (bool): Determines if tracking includes timing.
        """

        for key, value in kwargs.items():
            if key == "useData":
                if value:
                    self.write(f"sense:customofdm:trck:data:subcarriers 1")
                else:
                    self.write(f"sense:customofdm:trck:data:subcarriers 0")
            elif key == "amplitude":
                if value:
                    self.write(f"sense:customofdm:trck:amplitude 1")
                else:
                    self.write(f"sense:customofdm:trck:amplitude 0")
            elif key == "phase":
                if value:    
                    self.write(f"sense:customofdm:trck:phase 1")
                else:
                    self.write(f"sense:customofdm:trck:phase 0")
            elif key == "timing":
                if value:
                    self.write(f"sense:customofdm:trck:timing 1")
                else:
                    self.write(f"sense:customofdm:trck:timing 0")
            else:
                raise KeyError("Invalid keyword argument. Must be 'useData', 'amplitude', 'phase', or 'timing'.")

    def sanity_check(self):
        """Prints out measurement context-sensitive user-accessible class attributes."""

        print(f'Measurment mode: {self.meas}')
        if 'ddem' in self.meas.lower():
            print(f'Center frequency: {self.cf} Hz')
            print(f'Reference level: {self.amp} dBm')
            print(f'Modulation type: {self.modType}')
            print(f'Symbol rate: {self.symRate} symbols/sec')
            print(f'Measurement filter: {self.measFilter}')
            print(f'Reference filter: {self.refFilter}')
            print(f'Filter alpha: {self.filterAlpha}')
            print(f'Measurement length: {self.measLength} symbols')
            print(f'Equalizer state: {self.eqState}')
            print(f'Equalizer length: {self.eqLength} symbols')
            print(f'Equalizer convergence: {self.eqConvergence}')
        elif 'vect' in self.meas.lower():
            print(f'Center frequency: {self.cf} Hz')
            print(f'Reference level: {self.amp} dBm')
            print(f'Resolution bandwidth: {self.rbw} Hz')
            print(f'Acquisition time: {self.time} sec')
        else:
            pass
class VMA(socketscpi.SocketInstrument):
    """
    Generic class for controlling Keysight 89600 Vector Signal Analysis Software

    Attributes:
        cf (float): Analyzer center frequency in Hz
        atten (int): Attenuator value in dB
        ifGain (int): IF gain value in dB (-32 dB to +32 dB)
        amplifier (str): Amplifier state ('none', 'preamp', 'lna', 'lna+preamp')
        span (float): Analyzer span/info bandwidth in Hz
        meas (str): Measurement type ('VMA' currently supported)
    """

    def __init__(self, host, port=5025, timeout=10, reset=False, vsaHardware=None):
        super().__init__(host, port, timeout)

        # Set up hardware
        if not isinstance(vsaHardware, str) and vsaHardware is not None:
            raise error.VSAError('vsaHardware must be a string indicating which hardware platform to use.')

        self.hw = vsaHardware
        if vsaHardware is not None:
            self.set_hw(vsaHardware)

        if reset:
            # Reset and wait for reset to finish
            self.write('*rst')
            self.query('*opc?')

        self.write("instrument:select vma")
        self.write("configure:ofdm")
        self.write("configure:ofdm:ndefault")
        self.query('*opc?')

        # Pause measurement before doing anything
        self.write('initiate:pause')

        # Initialize global attributes
        self.cf = float(self.query('sense:ofdm:ccarrier0:reference?'))
        self.span = float(self.query('sense:ofdm:ccarrier0:bandwidth?'))
        
        self.meas = self.query('instrument:select?')

        # attenuation
        self.atten = int(self.query("sense:power:rf:attenuation?"))
        # if gain
        self.write("sense:ofdm:if:gain:auto:state off")
        self.write("sense:ofdm:if:gain:select other")
        self.ifGain = int(self.query("sense:ofdm:if:gain:level?"))
        # preamp
        self.preampBand = self.query('sense:power:rf:gain:band?').strip()
        self.preampState = self.query('sense:power:rf:gain:state?').strip()
        # uw path
        self.uwPath = self.query('sense:power:rf:mw:path?')

        # Initialize measurement-specific attributes.
        # OFDM
        self.time = 0

    def send_file_to_analyzer(self, sourcePath, destinationPath):
        """
        Sends a file from the controlling computer (remote) to the hard drive on the analyzer (local).

        Args:
            sourcePath (str): Absolute file path on local computer.
            destinationPath (str): Absolute destination file path on analyzer hard drive.
        """

        with open(sourcePath, mode="rb") as f:
            raw = f.read()
        try:
            self.write(f"mmemory:delete '{destinationPath}'")
            self.binblockwrite(f"mmemory:data '{destinationPath}', ", raw)
            self.err_check()
        except socketscpi.SockInstError as e:
            if 'already exists' not in str(e):
                raise socketscpi.SockInstError(str(e))

    def acquire_continuous(self):
        """Begins continuous acquisition in VMA using SCPI commands."""
        self.write('initiate:continuous on')
        self.write('initiate:immediate')

    def acquire_single(self):
        """Sets single acquisition mode and takes a single acquisition in VMA using SCPI commands."""
        self.write('initiate:continuous off')
        self.write('initiate:immediate')
        self.query('*opc?')

    def stop(self):
        """Stops acquisition in VMA using SCPI commands."""
        self.write('initiate:pause')

    def set_cf(self, cf):
        """
        Sets and reads center frequency for VMA using SCPI commands.

        Args:
            cf (float): Analyzer center frequency in Hz.
        """

        if not isinstance(cf, float) or cf <= 0:
            raise ValueError('Center frequency must be a positive floating point value.')

        self.write(f'sense:ofdm:carrier:reference {cf}')
        self.cf = float(self.query('sense:ofdm:carrier:reference?'))

        self.err_check()

    def set_span(self, span):
        """
        Sets and reads span for VMA using SCPI commands

        Args:
            span (float): Frequency span in Hz.
        """

        if not isinstance(span, float) and not isinstance(span, int):
            raise ValueError('Span must be a positive numerical value.')

        self.write(f'sense:frequency:span {span}')
        self.span = float(self.query('sense:frequency:span?'))

        self.err_check()

    def set_attenuation(self, atten):
        """
        Sets mechanical attenuator.

        Args:
            atten (int): Attenuator value in dB.
        """

        if not isinstance(atten, float) and not isinstance(atten, int):
            raise ValueError('"atten" must be a positive numerical value.')
        
        # Set mechanical attenuator value
        self.write(f"sense:power:rf:attenuation {atten}")
        self.atten = int(self.query("sense:power:rf:attenuation?"))

        self.err_check()

    def set_if_gain(self, ifGain):
        """
        Sets IF Gain value.

        Args:
            ifGain (int): IF Gain value in dB (range from -32 to +32).
        """

        if not isinstance(ifGain, float) and not isinstance(ifGain, int):
            raise ValueError('"ifGain" must be a numerical value.')

        self.write("sense:ofdm:if:gain:auto:state off")
        self.write("sense:ofdm:if:gain:select other")
        self.write(f"sense:ofdm:if:gain:level {ifGain}")
        self.ifGain = int(self.query("sense:ofdm:if:gain:level?"))

        self.err_check()
    
    def set_preamp_band(self, band):
        """
        Sets and gets preamp band.

        Args:
            band (str): Preamp band ('low'==<3.6 GHz, 'full'==>3.6 GHz).
        """

        if band.lower() not in ['low', 'full']:
            raise ValueError('"band" must be "low" or "full".')

        # Set preamp band and state
        self.write(f'sense:power:rf:gain:band {band}')
        self.preampBand = self.query('sense:power:rf:gain:band?')
        
        self.err_check()
        
    def set_preamp_state(self, state):
        """
        Sets and gets preamp state.

        Args:
            state (bool): Preamp state.
        """

        if not isinstance(state, bool):
            raise TypeError('"state" must be True or False.')

        # Sets preamp state
        if state:
            self.write(f'sense:power:rf:gain:state 1')
        else:
            self.write(f'sense:power:rf:gain:state 0')
        self.preampState = self.query('sense:power:rf:gain:state?')
        self.err_check()

    def set_uw_path(self, uwPath):
        """
        Sets and gets microwave path.
        
        Args:
            uwPath (str): Specifies microwave signal path ('std', 'lnp', 'mpb', 'full')
        """

        if uwPath.lower() not in ['std', 'lnp', 'mpb', 'full']:
            raise ValueError("'uwPath' must be 'std', 'lnp', 'mpb', or 'full'.")

        self.write(f'sense:power:rf:mw:path {uwPath}')
        self.uwPath = self.query('sense:power:rf:mw:path?')
        self.err_check()

    def set_signal_path(self, **kwargs):
        """
        Sets and reads attenuator, if gain, and amplifiers for VMA using SCPI commands.

        Args:
            preampBand (str): Preamp band ('low', 'full').
            preampState (bool): Preamp state (True, False).
            atten (int): Attenuator value in dB.
            ifGain (int): IF gain in dB.
            uwPath (str): Microwave path descriptor.
        """

        for key, value in kwargs.items():
            if key == 'preampBand':
                self.set_preamp_band(value)
            elif key == 'preampState':
                self.set_preamp_state(value)
            elif key == 'atten':
                self.set_attenuation(value)
            elif key == 'ifGain':
                self.set_if_gain(value)
            elif key == 'uwPath':
                self.set_uw_path(value)
        
        self.err_check()

    def evm_opt(self):
        """Executes an EVM optimization in VMA and waits for it to complete using SCPI commands."""

        # Gotta make sure measurement is running while doing this
        self.write('initiate:continuous on')
        self.write('initiate:immediate')

        self.write('sense:ofdm:optimize')
        self.query('*opc?')

        # Turn it back off when we're done
        self.write('initiate:continuous off')
        self.err_check()

    def load_demod_definition(self, definitionFile):
        """
        Loads an xml file generated from SignalStudio to configure the custom OFDM demod.
        
        Args:
            definitionFile (str): Absolute path to OFDM definition xml file.
        """

        self.write(f"mmemory:load:ofdm:setup CC0, '{definitionFile}'")
        self.query("*opc?")
        self.err_check()

    def ofdm_equalizer_setup(self, **kwargs):
        """Configures the equalizer settings for Custom OFDM.
        
        Args:
            useData (bool): Determines if the equalizer will use Data resource blocks for training.
            useDCPilot (bool): Determines if the equalizer will use DC Pilot for training.
            usePilot (bool): Determines if the equalizer will use Pilot resource blocks for training.
            usePreamble (bool): Determines if the equalizer will use Preamble resource blocks for training.
        """
 
        # useData=False, useDCPilot=False, usePilot=True, usePreamble=True
        for key, value in kwargs.items():
            if not isinstance(value, bool):
                raise TypeError(f'"{key}" must be True or False.')
            if key == "useData":
                if value:
                    self.write("sense:ofdm:ccarrier0:equalizer:use:data 1")
                else:
                    self.write("sense:ofdm:ccarrier0:equalizer:use:data 0")
            elif key == "useDCPilot":
                if value:
                    self.write(f"sense:ofdm:ccarrier0:equalizer:use:dcp 1")
                else:
                    self.write(f"sense:ofdm:ccarrier0:equalizer:use:dcp 0")
            elif key == "usePilot":
                if value:
                    self.write(f"sense:ofdm:ccarrier0:equalizer:use:pilot 1")
                else:
                    self.write(f"sense:ofdm:ccarrier0:equalizer:use:pilot 0")
            elif key == "usePreamble":
                if value:
                    self.write(f"sense:ofdm:ccarrier0:equalizer:use:preamble 1")
                else:
                    self.write(f"sense:ofdm:ccarrier0:equalizer:use:preamble 0")
            else:
                raise KeyError("Invalid keyword argument. Muse be 'useData', 'useDCPilot', 'usePilot', or 'usePreamble'.")

    def ofdm_tracking_setup(self, **kwargs):
        """Configures the tracking settings for Custom OFDM.
        
        Args:
            useData (bool): Determines if tracking includes data subcarriers.
            amplitude (bool): Determines if tracking includes amplitude.
            phase (bool): Determines if tracking includes phase.
            timing (bool): Determines if tracking includes timing.
        """

        for key, value in kwargs.items():
            if not isinstance(value, bool):
                raise TypeError(f'"{key}" must be True or False.')
            if key == "useData":
                if value:
                    self.write(f"sense:ofdm:ccarrier0:track:data 1")
                else:
                    self.write(f"sense:ofdm:ccarrier0:track:data 0")
            elif key == "amplitude":
                if value:
                    self.write(f"sense:ofdm:ccarrier0:track:amplitude 1")
                else:
                    self.write(f"sense:ofdm:ccarrier0:track:amplitude 0")
            elif key == "phase":
                if value:    
                    self.write(f"sense:ofdm:ccarrier0:track:phase 1")
                else:
                    self.write(f"sense:ofdm:ccarrier0:track:phase 0")
            elif key == "timing":
                if value:
                    self.write(f"sense:ofdm:ccarrier0:track:timing 1")
                else:
                    self.write(f"sense:ofdm:ccarrier0:track:timing 0")
            else:
                raise KeyError("Invalid keyword argument. Must be 'useData', 'amplitude', 'phase', or 'timing'.")

    def get_ofdm_results(self):
        """
        Reads OFDM results.
        """

        self.acquire_single()

        raw = [float(r) for r in self.query("fetch:ofdm?").split(',')]
        results = {'rmsEvm': raw[0], 'pkEvm': raw[1], 'pilotEvm': raw[2], 'dataEvm': raw[3], 'preambleEvm': raw[4], 'freqErr': raw[5], 'symClkErr': raw[6], 'rmsCpe': raw[7], 'syncCorr': raw[8], 'iqOffset': raw[9], 'iqQuadErr': raw[10], 'iqImb': raw[11], 'txPower': raw[12], 'allTxPower': raw[13], 'mer': raw[14]}
        
        return results
