"""
pyarbtools 0.1.0
error
Author: Morgan Allison, Keysight RF/uW Application Engineer
Updated: 10/18
Custom error classes for pyarbtools.
"""


class AWGError(Exception):
    """AWG Exception class"""


class VSGError(Exception):
    """Signal Generator Exception class"""


class BinblockError(Exception):
    """Binary Block Exception class"""
    pass


class SockInstError(Exception):
    """Socket Instrument Exception class"""
    pass
