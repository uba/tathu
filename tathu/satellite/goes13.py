#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import numpy as np

from tathu.binary import binary2raster

# Date format (old DSA/CPTEC File Naming Conventions)
DATE_REGEX = '\d{12}'
DATE_FORMAT = '%Y%m%d%H%M' # e.g. 201804081300 => 08 April 2018 - 13:00 UTC

# Data informations (TODO: read from CTL file)
NCOLS = 1870
NLINES = 1714
RES = 0.04
EXTENT = [-100, -56.04, -100 + (NCOLS * RES), -56.05 + (NLINES * RES)]
DATA_TYPE = np.int16

def sat2grid(path, autoscale=True):
    if(autoscale is False):
        return binary2raster(path, EXTENT, NLINES, NCOLS, DATA_TYPE)
    # else
    return binary2raster(path, EXTENT, NLINES, NCOLS,
        DATA_TYPE, np.float32, scale=1/100.0)
