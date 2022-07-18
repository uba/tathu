#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import numpy as np
from osgeo import gdal

from tathu.binary import binary2raster
from tathu.constants import KM_PER_DEGREE, LAT_LON_WGS84
from tathu.utils import getGeoT

# Date format (old DSA/CPTEC File Naming Conventions)
DATE_REGEX = '\d{12}'
DATE_FORMAT = '%Y%m%d%H%M' # e.g. 201804081300 => 08 April 2018 - 13:00 UTC

# Data informations (TODO: read from CTL file)
NCOLS = 1870
NLINES = 1714
RES = 0.04
EXTENT = [-100, -56.04, -100 + (NCOLS * RES), -56.05 + (NLINES * RES)]
DATA_TYPE = np.int16

def sat2grid(path, extent=None, resolution=4, autoscale=True, progress=None):
    if autoscale is False:
        grid = binary2raster(path, EXTENT, NLINES, NCOLS, DATA_TYPE)
    else:
        grid = binary2raster(path, EXTENT, NLINES, NCOLS,
            DATA_TYPE, np.float32, scale=1/100.0)

    if extent is None:
        return grid

    # else, remap to given extent...

    # Get memory driver
    memDriver = gdal.GetDriverByName('MEM')

    # Raster info
    dtype = grid.GetRasterBand(1).DataType
    print(dtype)
    fillValue = grid.GetRasterBand(1).GetNoDataValue()

    # Compute grid dimension
    sizex = int(((extent[2] - extent[0]) * KM_PER_DEGREE)/resolution)
    sizey = int(((extent[3] - extent[1]) * KM_PER_DEGREE)/resolution)
    print(sizex, sizey)

    # Create result
    remapped = memDriver.Create('grid', sizex, sizey, 1, dtype)

    # Adjust no-data
    if fillValue:
        remapped.GetRasterBand(1).SetNoDataValue(float(fillValue))
        remapped.GetRasterBand(1).Fill(float(fillValue))

    # Setup projection and geo-transformation
    remapped.SetProjection(LAT_LON_WGS84.ExportToWkt())
    remapped.SetGeoTransform(getGeoT(extent, sizey, sizex))

    # Perform the projection/resampling
    gdal.ReprojectImage(grid, remapped, LAT_LON_WGS84.ExportToWkt(),
        LAT_LON_WGS84.ExportToWkt(), gdal.GRA_NearestNeighbour,
        options=['NUM_THREADS=ALL_CPUS'], callback=progress)
        
    grid = None

    return remapped
