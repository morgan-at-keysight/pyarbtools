"""
vsaControl
Author: Morgan Allison, Keysight RF/uW Application Engineer
Generic VSA control object for PyArbTools.
"""

import socketscpi
import os
import warnings
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

    def set_measurement(self, meas):
        """
        Selects a measurement type in VSA using SCPI commands.

        Args:
            meas (str): Selects measurement type ('vector', 'ddemod' currently supported)
        """

        if meas.lower() not in ['vector', 'vect', 'ddemod', 'ddem']:
            raise ValueError('Invalid measurement selected. Choose \'vector\' or \'ddemod\'.')

        self.write('measure:nselect 1')
        self.write(f'measure:configure {meas}')
        self.meas = self.query('measure:configure?')

        if 'vect' in self.meas.lower():
            self.write('sense:rbw:points:auto 1')

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
            raise error.VSAError(f'Measurement type is currently "{self.meas}". Measurement type must be "vect" to configure digital demod.')

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

    def recall_recording(self, fileName, fileFormat='csv'):
        """
        Recalls a data file as a recording in VSA using SCPI commands.
        Args:
            fileName (str): Full absolute file name of the recording to be loaded.
            fileFormat (str): Format of recording file. ('CSV', 'E3238S', 'MAT', 'MAT7', 'N5110A', 'N5106A', 'SDF', 'TEXT')
        """

        if not os.path.exists(fileName):
            raise error.VSAError('Path or file name does not exist.')

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
