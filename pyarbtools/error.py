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


class VSAError(Exception):
    """VSA Exception class"""
    pass


class InstrumentError(Exception):
    """General Instrument Exception class"""
    pass