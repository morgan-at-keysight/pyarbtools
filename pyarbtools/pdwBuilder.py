"""
pdwBuilder
Author: Morgan Allison, Keysight RF/uW Application Engineer
Pulse Descriptor Word building functions for Analog and Vector UXGs.
"""

import math
import struct
import numpy as np
from pyarbtools import error


def convert_to_floating_point(inputVal, exponentOffset, mantissaBits, exponentBits):
    """
    HELPER FUNCTION NOT WRITTEN BY THE AUTHORS
    Computes modified floating point value represented by specified
    floating point parameters.
    fp = gain * mantissa^mantissaExponent * 2^exponentOffset

    Returns:
        Floating point value corresponding to passed parameters
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


def closest_m_2_n(inputVal, mantissaBits):
    """
    HELPER FUNCTION NOT WRITTEN BY THE AUTHORS
    Converts the specified value to the hardware representation in Mantissa*2^Exponent form

    Returns:
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


def chirp_closest_m_2_n(chirpRate, chirpRateRes=21.822):
    """
    HELPER FUNCTION NOT WRITTEN BY THE AUTHORS
    Convert the specified value to the hardware representation in Mantissa*2^Exponent form for Chirp parameters
    NOTE: I am not sure why the conversion factor of 21.82 needs to be there, but the math works out perfectly
    """

    output = np.uint32(0)
    mantissaBits = 13

    mantissaMask = np.uint32((1 << mantissaBits) - 1)
    # convert to clocks
    chirpValue = float(chirpRate) / float(chirpRateRes)
    success, exponent, mantissa = closest_m_2_n(chirpValue, mantissaBits)
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


def analog_bin_pdw_builder(operation=0, freq=1e9, phase=0, startTimeSec=0, width=0, powerLin=1, markers=0, pulseMode=2, phaseControl=0,
                    bandAdjust=0, chirpControl=0, code=0, chirpRate=0, freqMap=0):
    """
    This function builds a single format-1 PDW from a list of parameters.

    See User's Guide>Streaming Use>PDW Definitions section of
    Keysight UXG X-Series Agile Signal Generator Online Documentation
    http://rfmw.em.keysight.com/wireless/helpfiles/n519xa/n519xa.htm
    Args:
        operation (int): Specifies the operation of the PDW. (0-none, 1-first PDW, 2-last PDW)
        freq (float): CW frequency of PDW.
        phase (float): Phase of CW frequency of PDW.
        startTimeSec (float): Start time of the 50% rising edge power.
        width (float): Width of the pulse from 50% rise power to 50% fall power.
        powerLin (float): Linear scaling of the output in Vrms. (basically just leave this at 1)
        markers (int): Bit mask input of active markers (e.g. to activate marker 3, send the number 4, which is 0100 in binary).
        pulseMode (int): Configures pulse mode. (0-CW, 1-RF off, 2-Pulse enabled)
        phaseControl (int): Switches between phase mode. (0-coherent, 1-continuous)
        bandAdjust (int): Configures band adjustment criteria. (0-CW switch pts, 1-upper band, 2-lower band).
        chirpControl (int): Configures chirp shape. (0-stiched ramp, 1-triangle, 2-ramp)
        code (int): Selects hard-coded frequency/phase coding table index.
        chirpRate (float): Chirp rate in Hz/us.
        freqMap (int): Selects frequency band map. (0-A, 6-B)
    Returns:
        (NumPy array): Single PDW that can be used to build a PDW file or streamed directly to the UXG.
    """

    pdwFormat = 1
    _freq = int(freq * 1024 + 0.5)
    if 180 < phase <= 360:
        phase -= 360
    _phase = int(phase * 4096 / 360 + 0.5)
    _startTimePs = int(startTimeSec * 1e12)
    _widthNs = int(width * 1e9)
    _power = convert_to_floating_point(powerLin, -26, 10, 5)
    _chirpRate = chirp_closest_m_2_n(chirpRate)

    # Build PDW
    pdw = np.zeros(7, dtype=np.uint32)
    # Word 0: Mask pdw format (3 bits), operation (2 bits), and the lower 27 bits of freq
    pdw[0] = (pdwFormat | operation << 3 | (_freq << 5 & 0xFFFFFFFF))
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
def create_padding_block(sizeOfPaddingAndHeaderInBytes):
    """
    Creates an analog UXG binary padding block with header. The padding block
    is used to align binary blocks as needed so each block starts on a 16 byte
    boundary.  This padding block is also used to align PDW streaming data on
    4096 byte boundaries.

    Args:
        sizeOfPaddingAndHeaderInBytes (int): Total size of resulting padding
            binary block and header combined.
    Returns:
        binary block containing padding header and padded data
    """

    paddingHeaderSize = 16
    paddingFillerSize = sizeOfPaddingAndHeaderInBytes - paddingHeaderSize

    padBlockId = (1).to_bytes(4, byteorder='little')
    res3 = (0).to_bytes(4, byteorder='little')
    size = (paddingFillerSize).to_bytes(8, byteorder='little')
    # Padding Header Above = 16 bytes

    # X bytes of padding required to ensure PDW stream contents
    # (not PDW header) starts @ byte 4097 or (multiple of 4096)+1
    padData = (0).to_bytes(paddingFillerSize, byteorder='little')
    padding = [padBlockId, res3, size, padData]

    return padding


# noinspection PyDefaultArgument,PyRedundantParentheses,PyRedundantParentheses,PyRedundantParentheses,PyRedundantParentheses
def bin_freqPhaseCodingSingleEntry(onOffState=0, numBitsPerSubpulse=1, codingType=0, stateMapping=[0, 180],
                                   hexPatternString="E2", comment="default Comment"):
    """
    Creates a single entry binary frequency and phase coding block
    for analog UXG streaming.  This is only part of a full frequency and phase coding
    block with multiple entries for each pattern to be streamed to UXG.
        Args:
            onOffState (int): Activation state for current FPC entry
            numBitsPerSubpulse (int): = number of bits per subpulse.  E.g. For BPSK, this is 1
            codingType (int): 0=phase coding, 1= frequency coding, 2 = both phase and frequency coding
            stateMapping (double array): 2^numBitsPerSubpulse entries of phase / freq states
            hexPatternString (string):  Hex values to encode in FPC table e.g. "A2F4" multiple of 2 in length
            comment (string): FPC entry name

        Returns:
            binary array containing bytes for a single frequency phase entry

         TODO - Combination of simultaneous phase and frequency modulation not yet implemented
    """
    if ((len(hexPatternString) % 2) != 0):
        raise error.UXGError('Hex pattern length must be a multiple of 2: Length is ' + str(len(hexPatternString)))

    hexPatternBytes = bytearray.fromhex(hexPatternString)
    numBitsInPattern = 8 * len(hexPatternBytes)

    if (codingType != 0 and codingType != 1):
        raise error.UXGError('Only phase and frequency coding via streaming has been implemented in this example')
    if (numBitsPerSubpulse != 1):
        raise error.UXGError('Only one bit per subpulse has been implemented in this example')
    if (len(hexPatternBytes) > 8192):
        raise error.UXGError('Pattern must be less than 8192 bytes')
    if (len(comment) > 60):
        raise error.UXGError('Comment must be less than 60 characters long')

    entryState = onOffState.to_bytes(1, byteorder='little')
    numBitsPerSub = numBitsPerSubpulse.to_bytes(1, byteorder='little')
    modType = codingType.to_bytes(1, byteorder='little')
    numBytesInComment = len(comment).to_bytes(1, byteorder='little')
    numBitsInPat = numBitsInPattern.to_bytes(4, byteorder='little')

    fpcBin = entryState + numBitsPerSub + modType + numBytesInComment + numBitsInPat

    # Convert double array to little endian byte array - 8 bytes per double value
    for phaseOrFreq in stateMapping:
        doubleByteArrayPhase = bytearray(struct.pack("<d", phaseOrFreq))
        # arraySize = len(doubleByteArrayPhase)
        fpcBin = fpcBin + doubleByteArrayPhase

    fpcBin = fpcBin + hexPatternBytes

    # Translate comment to char[]
    commentEncoded = bytearray(comment, 'utf-8')
    fpcBin = fpcBin + commentEncoded

    return fpcBin


# noinspection PyRedundantParentheses,PyRedundantParentheses,PyRedundantParentheses,PyRedundantParentheses
def bin_pdw_freqPhaseCodingBlock():
    """
    Creates a complete frequency and phase coding block containing header and data
    for analog UXG streaming.
    This block is used to describe variable length pulse frequency/phase coding setups.
    This allows frequency and phase coding tables to be updated over ethernet streaming
    instead of having to send SCPI commands.
    http://rfmw.em.keysight.com/wireless/helpfiles/n519xa/n519xa.htm#User's%20Guide/Streaming%20Mode%20File%20Format%20Definition.htm%3FTocPath%3DUser's%2520Guide%7CStreaming%2520Mode%2520Use%7C_____5

    currently hardcoded to create FCP block with 3 fixed entries
           first  entry is index 0 in FPC table - no coding
           second entry is index 1 in FPC table - PSK
           third  entry is index 2 in FPC table - FSK

    Returns (bytearray):
        Bytearray containing full FCP block with header.
    """

    numEntries = 3

    freqPhaseBlockId = (13).to_bytes(4, byteorder='little')
    reserved1 = (0).to_bytes(4, byteorder='little')
    # Size calculated last
    version = (2).to_bytes(4, byteorder='little')
    numberOfEntries = numEntries.to_bytes(4, byteorder='little')

    entry0 = bin_freqPhaseCodingSingleEntry(0, 1, 0, [0, 180], "", "NoCodingFirstEntry")
    entry1 = bin_freqPhaseCodingSingleEntry(1, 1, 0, [0, 180], "2A61D327", "PSKcode32bits")
    entry2 = bin_freqPhaseCodingSingleEntry(1, 1, 1, [-10e6, 10e6], "5AC4", "FSKcodeTest16bits")

    # Size does not include blockID and reserved fields 8 bytes
    sizeInBytes = len(version) + len(numberOfEntries) + len(entry0) + len(entry1) + len(entry2)
    sizeBlock = sizeInBytes.to_bytes(8, byteorder='little')

    returnBlock = [freqPhaseBlockId, reserved1, sizeBlock, version, numberOfEntries, entry0, entry1, entry2]

    # fpcBlock size must be a multiple of 16 to be on proper byte boundary - Add padding as needed
    tempSize = len(b''.join(returnBlock))
    sizeOfEndBufferBytes = 16 - (tempSize % 16)
    endFpcBlockBufferBytes = (0).to_bytes(sizeOfEndBufferBytes, byteorder='little')

    returnBlockWithPadding = [freqPhaseBlockId, reserved1, sizeBlock, version, numberOfEntries, entry0, entry1, entry2,
                              endFpcBlockBufferBytes]

    return returnBlockWithPadding


# noinspection PyRedundantParentheses
def analog_bin_pdw_file_builder(pdwList):
    """
    Builds a binary PDW file with a padding block to ensure the
    PDW section begins at an offset of 4096 bytes (required by UXG).

    See User's Guide>Streaming Use>PDW File Format section of
    Keysight UXG X-Series Agile Signal Generator Online Documentation
    http://rfmw.em.keysight.com/wireless/helpfiles/n519xa/n519xa.htm
    Args:
        pdwList (list): List of lists. Each inner list contains a single pulse descriptor word.

    Returns:
        (bytes): Binary data that contains a full PDW file that can be downloaded to and played out of the UXG.
    """

    # Include frequency phase coding block flag: 1 = yes, 0 = no
    includeFpcBlock = 1

    # Header section, all fixed values
    fileId = b'STRM'
    version = (1).to_bytes(4, byteorder='little')

    # First field is first block of 4096 bytes.  If frequency phase coding block is large,
    # this offset to the start of PDW data might extend past first 4096 sized block
    fieldBlock = 1
    offset = ((fieldBlock >> 1) & 0x3fffff).to_bytes(4, byteorder='little')

    magic = b'KEYS'
    res0 = (0).to_bytes(16, byteorder='little')
    flags = (0).to_bytes(4, byteorder='little')
    uniqueId = (0).to_bytes(4, byteorder='little')
    dataId = (16).to_bytes(4, byteorder='little')
    res1 = (0).to_bytes(4, byteorder='little')
    header = [fileId, version, offset, magic, res0, flags, uniqueId, dataId, res1]
    tempHeaderSize = len(b''.join(header))

    # FPC Block - skip fpcBlock if flag is zero
    fpcBlock = [b'']
    if (includeFpcBlock):
        fpcBlock = bin_pdw_freqPhaseCodingBlock()
    fpcBlockSize = len(b''.join(fpcBlock))

    # PDW block header must start at byte 4080 so PDW stream data starts at byte 4097
    paddingSize = 4080 - tempHeaderSize - fpcBlockSize
    paddingBlock = create_padding_block(paddingSize)

    # PDW block header = 16 bytes
    pdwBlockId = (16).to_bytes(4, byteorder='little')
    res4 = (0).to_bytes(4, byteorder='little')

    sizeOfPdwInBytes = 28
    pdwDataSizeInBytes = sizeOfPdwInBytes * len(pdwList)
    pdwSize = (pdwDataSizeInBytes).to_bytes(8, byteorder='little')
    # This results in null pdws for 8 zero bytes added later
    #pdwSize = (0xffffffffffffffff).to_bytes(8, byteorder='little')

    # Build Raw PDW Data from list
    rawPdwData = [analog_bin_pdw_builder(*p) for p in pdwList]
    # Add 8 bytes of zero to make sure PDW block ends on 16 byte boundary.
    rawPdwData += [(0).to_bytes(8, byteorder='little')]
    rawPdwData = b''.join(rawPdwData)
    pdwBlock = [pdwBlockId, res4, pdwSize, rawPdwData]

    pdwEndBlock = [(0).to_bytes(16, byteorder='little')]

    # Build PDW file from header, padBlock, pdwBlock, and PDWs
    pdwFile = header + fpcBlock + paddingBlock + pdwBlock + pdwEndBlock

    # Convert arrays of data to a single byte-type variable
    pdwFile = b''.join(pdwFile)

    return pdwFile


def vector_bin_pdw_builder_rev3b(operation=0, freq=1e9, phase=0, startTimeSec=0,
                                 width=0, maxPower=0, markers=0, powerDbm=0,
                                 phaseControl=0, rfOff=0, autoBlank=1,
                                 newWaveform=1, zeroHold=0, loLead=0, wfmMkrMask=0,
                                 wIndex=0, power2dBm=0, maxPower2dBm=0, dopplerHz = 0):
    """
    This function builds a single format-3 PDW Rev B (fw A.01.30 and later)
    from a list of parameters.

    See User's Guide>Streaming Use>PDW Definitions section of
    Keysight UXG X-Series Agile Vector Adapter Online Documentation
    http://rfmw.em.keysight.com/wireless/helpfiles/n519xa-vector/n519xa-vector.htm
    Args:
        operation (int): Specifies the operation of the PDW.
                        (0-none, 1-first PDW, 2-last PDW)
        freq (float): CW frequency of PDW.
        phase (float): Phase of CW frequency of PDW.
        startTimeSec (float): Start time of the 50% rising edge power.
        width (float): Width of the pulse from 50% rise power
                        to 50% fall power seconds.
        maxPower (float): Max output power in dBm.
        markers (int): Enables or disables PDW markers via bit masking.
                        (e.g. to activate marker 3, send the number 4,
                        which is 0100 in binary).
        powerDbm (float): Sets power for individual PDW in dBm.
        phaseControl (int): Switches between phase mode.
                        (0-coherent, 1-continuous)
        rfOff (int): Activates or deactivates RF Off mode.
                        (0-RF on, 1-RF off).
                        Note: This nomenclature is not intuitive.
        autoBlank (int): Activates blanking. (0-no blanking, 1-blanking)
        newWaveform (int): (0-continue with prior PDW settings,
                            1-start with all new pdw settings)
        zeroHold (int): Selects zero/hold behavior.
                        (0-zero, 1-hold last value)
        loLead (float): Specifies how long before the PDW start time to
                        begin switching LO.
        wfmMkrMask (int): Enables or disables waveform markers via bit
                            masking. (e.g. to activate marker 3, send the
                            number 4, which is 0100 in binary).
        wIndex (int): Index of the IQ waveform to be assigned to the PDW.
        power2dBm (float): Alternate (second) desired output power in dBm - pdw Rev B
        maxPower2dBm (float): Alternate max power output - pdw Rev B
        dopplerHz (float): Doppler frequency - pdw Rev B

    Returns:
        (NumPy array): Single PDW that can be used to build a PDW file or streamed
                        directly to the UXG.
    """
    pdwFormat = 3
    _freq = int(freq * 1024 + 0.5)
    _phase = int(phase * 4096 / 360 + 0.5)
    _startTimePs = int(startTimeSec * 1e12)
    _pulseWidthInHalfNs = int(width * 1e9 * 2)
    _maxPower = int((maxPower + 140) / 0.005 + 0.5)
    _power = int((powerDbm + 140) / 0.005 + 0.5)
    _loLead = int(loLead / 4e-9)
    _newWfm = newWaveform
    _wfmType = 0
    _power2 = int((power2dBm + 140) / 0.005 + 0.5)
    _maxPower2 = int((maxPower2dBm + 140) / 0.005 + 0.5)
    _doppler = int(dopplerHz + 0.5)

    # Build PDW
    pdw = np.zeros(12, dtype=np.uint32)
    # Word 0: Mask pdw format (3 bits), operation (2 bits), freqLower (27 bits)
    pdw[0] = (pdwFormat | operation << 3 | _freq << 5) & 0xFFFFFFFF
    # Word 1: freqUpper (20 bits 47-27) of freq and phase (12 bits)
    pdw[1] = (_freq >> 27 | _phase << 20) & 0xFFFFFFFF
    # Word 2: Lower 32 bits of startTimePs
    pdw[2] = _startTimePs & 0xFFFFFFFF
    # Word 3: Upper 32 bits of startTimePS
    pdw[3] = (_startTimePs & 0xFFFFFFFF00000000) >> 32
    # Word 4: Lower 32 bits of Pulse width (37 bits)
    pdw[4] = _pulseWidthInHalfNs & 0xFFFFFFFF
    # Word 5: Upper 5 bits of Pulse width, max power (15 bits), markers (12 bits)
    pdw[5] = (_pulseWidthInHalfNs & 0x1F00000000) >> 32 | \
             _maxPower << 5 | markers << 20
    # Word 6: Power (15 bits), phase mode (1), RF off (1), auto blank (1),
    #           new wfm (1), zero/hold (1), lo lead (8), marker mask (4)
    pdw[6] = _power | phaseControl << 15 | rfOff << 16 | autoBlank << 17 |\
             _newWfm << 18 | zeroHold << 19 | _loLead << 20 | wfmMkrMask << 28
    # Word 7: Reserved (8), Wfm type (2), index (16), power2low (6)
    pdw[7] = (_wfmType << 8 | wIndex << 10 | _power2 << 26) & 0xFFFFFFFF
    # Word 8: power2high (9), max power (15), reserved (8)
    pdw[8] = _power2 >> 6 | _maxPower2 << 9
    # Word 9: reserved (16), reserved (16)
    pdw[9] = 0
    # Word 10: reserved (4), reserved (2), reserved (17), dopplerLow (9)
    pdw[10] = (_doppler << 23) & 0xFFFFFFFF
    # Word 11: dopplerHigh (12), reserved (11), reserved (9)
    pdw[11] = _doppler >> 9

    return pdw


def vector_bin_pdw_builder(operation, freq, phase, startTimeSec, powerDbm,
                           markers, phaseControl, rfOff, wIndex, wfmMkrMask):
    """
    This function builds a single format-1 PDW from a list of parameters.
    PDW format-1 is now deprecated.  This format is still supported as legacy

    See User's Guide>Streaming Use>PDW Definitions section of
    Keysight UXG X-Series Agile Vector Adapter Online Documentation
    http://rfmw.em.keysight.com/wireless/helpfiles/n519xa-vector/n519xa-vector.htm
    Args:
        operation (int): Specifies the operation of the PDW.
                         (0-none, 1-first PDW, 2-last PDW)
        freq (float): CW frequency of PDW.
        phase (float): Phase of CW frequency of PDW.
        startTimeSec (float): Start time of the 50% rising edge power.
        powerDbm (float): Sets power for individual PDW in dBm.
        markers (int): Enables or disables PDW markers via bit masking.
                       (e.g. to activate marker 3, send the number 4,
                       which is 0100 in binary).
        phaseControl (int): Switches between phase mode. (0-coherent, 1-continuous)
        rfOff (int): Activates or deactivates RF Off mode. (0-RF on, 1-RF off).
                     I know, the nomenclature here is TRASH.
        wIndex (int): Index of the IQ waveform to be assigned to the PDW.
        wfmMkrMask (int): Enables or disables waveform markers via bit masking.
                          (e.g. to activate marker 3, send the number 4,
                          which is 0100 in binary).

    Returns:
        (NumPy array): Single PDW that can be used to build a PDW file or
                       streamed directly to the UXG.
    """

    # Format 1 PDWs are deprecated
    pdwFormat = 1
    _freq = int(freq * 1024 + 0.5)
    _phase = int(phase * 4096 / 360 + 0.5)
    _startTimePs = int(startTimeSec * 1e12)
    _power = int((powerDbm + 140) / 0.005 + 0.5)

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


def vector_build_raw_pdw_block_rev3B(pdwList):
    """
    Builds a raw binary pdw block without header

    See User's Guide>Streaming Use>PDW Definitions section of
    Keysight UXG X-Series Agile Vector Adapter Online Documentation
    http://rfmw.em.keysight.com/wireless/helpfiles/n519xa-vector/n519xa-vector.htm
    Args:
        pdwList (list): List of lists. Each inner list contains a single
    pulse descriptor word.

    Returns:
        (bytes): Binary data that contains a raw PDW binary block
                 without header.  This can be streamed directly to UXG
    """
    pdwData = []
    pdwData += [vector_bin_pdw_builder_rev3b(*p) for p in pdwList]
    # Convert arrays of data to a single byte-type variable
    pdwData = b''.join(pdwData)

    return pdwData


# noinspection PyRedundantParentheses
def vector_bin_pdw_file_builder(pdwList):
    """
    Builds a binary PDW file with a padding block to ensure the
    PDW section begins at an offset of 4096 bytes (required by UXG).

    See User's Guide>Streaming Use>PDW Definitions section of
    Keysight UXG X-Series Agile Vector Adapter Online Documentation
    http://rfmw.em.keysight.com/wireless/helpfiles/n519xa-vector/n519xa-vector.htm
    Args:
        pdwList (list): List of lists. Each inner list contains a single
    pulse descriptor word.

    Returns:
        (bytes): Binary data that contains a full PDW file that can
            be downloaded to and played out of the UXG.
    """

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

    # PDW format 3 rev B 12 is 32 bit words
    sizeOfPdwInBytes = 48
    pdwDataSizeInBytes = sizeOfPdwInBytes * len(pdwList)
    # File corrupt with this approach - more testing needed
    #pdwSize = (pdwDataSizeInBytes).to_bytes(8, byteorder='little')

    # PDWs make up remainder of file.
    pdwSize = (0xffffffffffffffff).to_bytes(8, byteorder='little')

    pdwBlock = [pdwBlockId, res4, pdwSize]
    pdwData = [vector_bin_pdw_builder_rev3b(*p) for p in pdwList]
    pdwBlock += pdwData

    # Build PDW file from header, padBlock, pdwBlock, and PDWs
    pdwFile = header + padding + pdwBlock

    # Convert arrays of data to a single byte-type variable
    pdwFile = b''.join(pdwFile)

    return pdwFile
