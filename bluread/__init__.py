"""
PyBluRead is a wrapper around libbluray.
By Colin ML Burnett

Not everything in libbluray is wrapped by this library.
"""

import _bluread

__all__ = ["Bluray", "Title", "Version"]

Version = _bluread.Version

from .objects import Bluray, Title

