#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""TATHU - Tracking and Analysis of Thunderstorms."""

from .logo import TATHU_ASCII_LOGO
from .version import __version__

__all__ = (
    '__version__',
)

print(TATHU_ASCII_LOGO)
