#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

'''
Module for reading NCEP/CPC 4km Global (60N - 60S) IR Dataset.
README: http://www.cpc.ncep.noaa.gov/products/global_precip/html/README
The data contain globally-merged (60S-60N) 4-km pixel-resolution IR brightness temperature
data (equivalent blackbody temperatures), merged from the European, Japanese, and U.S.
geostationary satellites over the period of record (GOES-8/9/10/11/12/13/14/15/16,
METEOSAT-5/7/8/9/10, and GMS-5/MTSat-1R/2/Himawari-8).
Every netCDF-4 file covers one hour, and contains two half-hourly grids, at 4-km grid cell resolution.
'''

from datetime import timedelta
from enum import Enum

import numpy as np
from netCDF4 import Dataset
from osgeo import gdal

from tathu.constants import KM_PER_DEGREE, LAT_LON_WGS84
from tathu.utils import array2raster, file2timestamp, fill, getGeoT

# Date format
DATE_REGEX = '\d{10}'
DATE_FORMAT = '%Y%m%d%H' # e.g. 2018040813 => 08 April 2018 - 13:00 UTC

class CompositionTime(Enum):
    ON_THE_HOUR = 0
    ON_THE_HALF_HOUR = 1
    def __str__(self):
        return self.name

def getTimestamp(path, time=CompositionTime.ON_THE_HOUR):
    date = file2timestamp(path, regex=DATE_REGEX, format=DATE_FORMAT)
    if time is CompositionTime.ON_THE_HOUR:
        return date
    return date + timedelta(minutes=30)

def getExtent(path):
    nc = Dataset(path)
    lat = nc.variables['lat'][:]
    lon = nc.variables['lon'][:]
    llx, lly = np.min(lon), np.min(lat)
    urx, ury = np.max(lon), np.max(lat)
    return [llx, lly, urx, ury]

def sat2grid(path, time=CompositionTime.ON_THE_HOUR, extent=None, resolution=4, progress=None, fillNoDataValues=False):
    # Get full-extent
    full_extent = getExtent(path)

    # Read data
    nc = Dataset(path)
    data = np.flipud(nc.variables['Tb'][time.value,:,:])

    # Create grid object using GDAL
    grid = array2raster(data, full_extent, nodata=nc.variables['Tb']._FillValue)

    # Fill no-data values if requested. i.e. fill missing values with nearest neighbour
    if fillNoDataValues:
        nodata = grid.GetRasterBand(1).GetNoDataValue()
        array = grid.ReadAsArray()
        array[array == nodata] = np.nan
        array = fill(array)
        grid.GetRasterBand(1).WriteArray(array)

    # Need remap?
    if extent is None:
        return grid

    # else, remap to given extent...

    # Get memory driver
    memDriver = gdal.GetDriverByName('MEM')

    # Raster info
    dtype = grid.GetRasterBand(1).DataType
    fillValue = grid.GetRasterBand(1).GetNoDataValue()

    # Compute grid dimension
    sizex = int(((extent[2] - extent[0]) * KM_PER_DEGREE)/resolution)
    sizey = int(((extent[3] - extent[1]) * KM_PER_DEGREE)/resolution)

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
