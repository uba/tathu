#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import gzip
import os

import numpy as np

from tathu.utils import array2raster

def read(path, nlines, ncols, dtype=np.int16):
    _, ext = os.path.splitext(path)
    if ext.lower() == '.gz':
        with gzip.open(path, 'rb') as f:
            array = np.frombuffer(f.read(), dtype=dtype)
    else:
        array = np.fromfile(path, dtype, nlines * ncols)
    return array.reshape((nlines, ncols))

def binary2raster(path, extent, nlines, ncols, dtype, ctype=None, scale=1.0, offset=0.0):
    array = read(path, nlines, ncols, dtype)
    if(ctype and ctype != dtype):
        # Conversion requested. Transform data type and apply scale/offset
        array = array.astype(ctype)
        array = array * scale + offset
    return array2raster(array, extent)
