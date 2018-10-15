"""
pyarbtools 0.1.0
Socket Instrument Class
Author: Morgan Allison
Updated: 10/18
This program provides a socket interface to Keysight test equipment.
It handles sending commands, receiving query results, and
reading/writing binary block data.
Windows 7 64-bit
Python 3.6.4 64-bit
NumPy 1.14.2
"""

import socket
import numpy as np


class BinblockError(Exception):
    """Binary Block Exception class"""
    pass


class SockInstError(Exception):
    """Socket Instrument Exception class"""
    pass


class SocketInstrument:
    def __init__(self, host, port, timeout=10):
        """Open socket connection with settings for instrument control."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        self.socket.settimeout(timeout)
        self.socket.connect((host, port))

        self.instId = self.query('*idn?')

    def disconnect(self):
        """Gracefully close connection."""
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def query(self, cmd):
        """Sends query to instrument and returns reply as string."""
        # self.write(cmd)

        msg = '{}\n'.format(cmd)
        self.socket.send(msg.encode('latin_1'))

        # Read continuously until termination character is found.
        response = b''
        while response[-1:] != b'\n':
            response += self.socket.recv(1024)

        # Strip out whitespace and return.
        return response.decode('latin_1').strip()

    def write(self, cmd):
        """Write a command string to instrument."""
        msg = '{}\n'.format(cmd)
        self.socket.send(msg.encode('latin_1'))
        # msg = '{}\n*esr?'.format(cmd)
        # ret = self.query(msg)
        # if (int(ret) != 0):
        #     raise SockInstError('esr non-zero: {}'.format(ret))

    def err_check(self):
        """Prints out all errors and clears error queue.

        Certain instruments format the syst:err? response differently, so remove whitespace and
        extra characters before checking."""
        err = []
        temp = self.query('syst:err?').strip().replace('+', '').replace('-', '')
        while temp != '0,"No error"':
            # print(temp)
            err.append(temp)
            temp = self.query('syst:err?').strip().replace('+', '').replace('-', '')
        # print(self.query('syst:err?'))
        if err:
            raise SockInstError(err)

    def binblockread(self, dtype=np.int8, debug=False):
        """Read data with IEEE 488.2 binary block format

        The waveform is formatted as:
        #<x><yyy><data><newline>, where:
        <x> is the number of y bytes. For example, if <yyy>=500, then <x>=3.
        NOTE: <x> is a hexadecimal number.
        <yyy> is the number of bytes to transfer. Care must be taken
        when selecting the data type used to interpret the data.
        The dtype argument used to read the data must match the data
        type used by the instrument that sends the data.
        <data> is the curve data in binary format.
        <newline> is a single byte new line character at the end of the data.
        """

        # Read # character, raise exception if not present.
        if self.socket.recv(1) != b'#':
            raise BinblockError('Data in buffer is not in binblock format.')

        # Extract header length and number of bytes in binblock.
        headerLength = int(self.socket.recv(1).decode('latin_1'), 16)
        numBytes = int(self.socket.recv(headerLength).decode('latin_1'))

        if debug:
            print('Header: #{}{}'.format(headerLength, numBytes))

        rawData = bytearray(numBytes)
        buf = memoryview(rawData)

        # While there is data left to read...
        while numBytes:
            # Read data from instrument into buffer.
            bytesRecv = self.socket.recv_into(buf, numBytes)
            # Slice buffer to preserve data already written to it.
            buf = buf[bytesRecv:]
            # Subtract bytes received from total bytes.
            numBytes -= bytesRecv
            if debug:
                print('numBytes: {}, bytesRecv: {}'.format(
                    numBytes, bytesRecv))

        # Receive termination character.
        term = self.socket.recv(1)
        if debug:
            print('Term char: ', term)
        # If term char is incorrect or not present, raise exception.
        if term != b'\n':
            print('Term char: {}, rawData Length: {}'.format(
                term, len(rawData)))
            raise BinblockError('Data not terminated correctly.')

        # Convert binary data to NumPy array of specified data type and return.
        return np.frombuffer(rawData, dtype=dtype)

    def binblock_header(self, data):
        """Returns a IEEE 488.2 binary block header

        #<x><yyy>..., where:
        <x> is the number of y bytes. For example, if <yyy>=500, then <x>=3.
        NOTE: <x> is a hexadecimal number.
        <yyy> is the number of bytes to transfer. """

        numBytes = memoryview(data).nbytes
        return f'#{len(str(numBytes))}{numBytes}'

    def binblockwrite(self, msg, data, debug=False, esr=True):
        """Send data with IEEE 488.2 binary block format

        The data is formatted as:
        #<x><yyy><data><newline>, where:
        <x> is the number of y bytes. For example, if <yyy>=500, then <x>=3.
        NOTE: <x> is a hexadecimal number.
        <yyy> is the number of bytes to transfer. Care must be taken
        when selecting the data type used to interpret the data.
        The dtype argument used to read the data must match the data
        type used by the instrument that sends the data.
        <data> is the curve data in binary format.
        <newline> is a single byte new line character at the end of the data.
        """

        header = self.binblock_header(data)

        # Send message, header, data, and termination
        self.socket.send(msg.encode('latin_1'))
        self.socket.send(header.encode('latin_1'))
        self.socket.send(data)
        self.socket.send(b'\n')

        if debug:
            print(f'binblockwrite --')
            print(f'msg: {msg}')
            print(f'header: {header}')

        # Check error status register and notify of problems
        if esr:
            r = self.query('*esr?')
            if int(r) is not 0:
                print(r)
                self.err_check()
                # raise BinblockError(f'Non-zero ESR: {r}')


def awg_example(ipAddress, port=5025):
    """Tests generic waveform transfer to M8190. Length and granularity checks not performed."""
    awg = SocketInstrument(host=ipAddress, port=port, timeout=10)
    print(awg.instId)

    awg.write('*rst')
    awg.query('*opc?')

    fs = 10e9
    freq = 100e6
    res = 'wsp'

    awg.write('func:mode arb')
    awg.write(f'trace1:dwidth {res}')
    awg.write(f'frequency:raster {fs}')

    awg.write('output1:route dac')
    awg.write('output1:norm on')

    rl = fs / freq * 64
    t = np.linspace(0, rl / fs, rl, endpoint=False)
    wfm = np.array(2047 * np.sin(2 * np.pi * freq * t), dtype=np.int16) << 4

    awg.write(f'trace:def 1, {rl}')
    awg.binblockwrite('trace:data 1, 0, ', wfm)

    awg.write('trace:select 1')
    awg.write('init:cont on')
    awg.write('init:imm')
    awg.query('*opc?')

    awg.err_check()
    awg.disconnect()


def vna_example(ipAddress, port=5025):
    """Test generic VNA connection, sweep control, and data transfer."""
    vna = SocketInstrument(host=ipAddress, port=port, timeout=10)
    print(vna.instId)

    vna.write('system:fpreset')
    vna.query('*opc?')

    measName = 'meas1'
    vna.write('display:window1:state on')
    vna.write(f'calc1:parameter:define "{measName}", "S11"')
    vna.write(f'display:window1:trace1:feed "{measName}"')
    vna.write(f'calc1:parameter:select "{measName}"')

    vna.write('initiate:continuous off')
    vna.write('initiate:immediate')
    vna.query('*opc?')
    vna.write('display:window1:y:auto')

    vna.write('format:border swap')
    vna.write('format real,64')

    vna.write('calculate1:data? fdata')
    meas = vna.binblockread(dtype=np.float64)
    vna.query('*opc?')

    vna.write('calculate1:x?')
    freq = vna.binblockread(dtype=np.float64)
    vna.query('*opc?')

    vna.err_check()
    vna.disconnect()

    return freq, meas


def main():
    # awg_example('10.112.181.139', port=5025)
    vna_example('10.112.181.177', port=5025)


if __name__ == '__main__':
    main()
