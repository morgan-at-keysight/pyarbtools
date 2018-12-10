"""
pyarbtools 0.0.10
error
Author: Morgan Allison, Keysight RF/uW Application Engineer
Custom error classes for pyarbtools.
"""


class GranularityError(Exception):
    """Waveform Granularity Exception class"""


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
