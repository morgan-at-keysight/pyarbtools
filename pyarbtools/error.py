"""
error
Author: Morgan Allison, Keysight RF/uW Application Engineer
Custom error classes for pyarbtools.
"""


class WfmBuilderError(Exception):
    """Waveform Builder Exception class"""
    pass


class GranularityError(Exception):
    """Waveform Granularity Exception class"""
    pass


class AWGError(Exception):
    """AWG Exception class"""
    pass


class VSGError(Exception):
    """Signal Generator Exception class"""
    pass


class VXGError(Exception):
    """VXG Exception class"""
    pass


class UXGError(Exception):
    """UXG Exception class"""
    pass


class VSAError(Exception):
    """VSA Exception class"""
    pass

# class BinblockError(Exception):
#     """Binary Block Exception class"""
#     pass
#
#
# class SockInstError(Exception):
#     """Socket Instrument Exception class"""
#     pass
