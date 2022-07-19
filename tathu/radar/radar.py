#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import numpy as np
from osgeo import gdal

import tathu.binary
from tathu.utils import getGeoT

def read(path, extent, nlines, ncols):
    # Read data
    data = tathu.binary.read(path, nlines, ncols, dtype=np.float32)
    data = np.flipud(data)
    
    # Create GDAL raster in memory
    driver = gdal.GetDriverByName('MEM')
    raster = driver.Create('radar', ncols, nlines, 1, gdal.GDT_Float32)
    raster.SetGeoTransform(getGeoT(extent, nlines, ncols))
    raster.GetRasterBand(1).WriteArray(data)
    raster.FlushCache()

    return raster
