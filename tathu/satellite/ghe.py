#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import numpy as np
from netCDF4 import Dataset

from tathu.utils import array2raster

'''
Operational Hydro-Estimator Satellite Rainfall Estimates
https://noaa-ghe-pds.s3.amazonaws.com/index.html#rain_rate
'''

# Date format
DATE_REGEX = '\d{12}'
DATE_FORMAT = '%Y%m%d%H%M' # e.g. 2018040813 => 08 April 2018 - 13:00 UTC
GLOBAL_EXTENT = [-180.0, -65.0, 180.0, 65.0]

def sat2grid(path):
    nc = Dataset(path)
    data = nc.variables['rain'][:]
    data = np.ma.masked_where(data < nc.variables['rain'].valid_range[0], data)
    data = np.ma.masked_where(data > nc.variables['rain'].valid_range[1], data)
    return array2raster(data, GLOBAL_EXTENT, nodata=nc.variables['rain']._FillValue)
