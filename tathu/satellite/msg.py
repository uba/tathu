#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import numpy as np
from netCDF4 import Dataset
from osgeo import gdal, osr

from tathu.constants import KM_PER_DEGREE
from tathu.utils import getGeoT

# MSG Spatial Reference System (proj4 string format)
MSGProj4 = '+proj=geos +h=35785831.0 +a=6378137.0 +b=6378169.0 +f=0.00338423143 +lat_0=0.0 +lon_0=0.0 +sweep=y +no_defs'

def getScaleOffset(path):
    nc = Dataset(path, mode='r')
    scale = nc.variables['z'].scale_factor
    offset = 0
    nc.close()
    return scale, offset

def getProjExtent(path):
    nc = Dataset(path, mode='r')
    llx = nc.variables['x'][0]
    lly = nc.variables['y'][0]
    urx = nc.variables['x'][-1]
    ury = nc.variables['y'][-1]
    nc.close()
    return [llx, lly, urx, ury]

def getFillValue(path):
    nc = Dataset(path, mode='r')
    value = nc.variables['z']._FillValue
    nc.close()
    return float(value)

def sat2grid(path, extent, resolution, targetPrj, driver, scale=None, offset=None, progress=None, options=['NUM_THREADS=ALL_CPUS']):
    # Read scale/offset from file, if necessary
    if scale is None or offset is None:
        scale, offset = getScaleOffset(path)

    # Extract MSG projection extent
    msgProjExtent = getProjExtent(path)

    # Build connection info based on given driver name
    if driver == 'NETCDF':
        connectionInfo = 'NETCDF:\"' + path + '\":z'
    else: # HDF5
        connectionInfo = 'HDF5:\"' + path + '\"://z'

    # Open NetCDF file (MSG data)
    raw = gdal.Open(connectionInfo, gdal.GA_ReadOnly)

    # MSG spatial reference system
    sourcePrj = osr.SpatialReference()
    sourcePrj.ImportFromProj4(MSGProj4)

    # get fill-value
    FillValue = getFillValue(path)

    # Setup projection and geo-transformation
    raw.SetProjection(sourcePrj.ExportToWkt())
    raw.SetGeoTransform(getGeoT(msgProjExtent, raw.RasterYSize, raw.RasterXSize))
    raw.GetRasterBand(1).SetNoDataValue(FillValue)

    # Compute grid dimension
    sizex = int(((extent[2] - extent[0]) * KM_PER_DEGREE) / resolution)
    sizey = int(((extent[3] - extent[1]) * KM_PER_DEGREE) / resolution)

    # Get memory driver
    memDriver = gdal.GetDriverByName('MEM')

    # Create grid
    grid = memDriver.Create('grid', sizex, sizey, 1, gdal.GDT_Float32)
    grid.GetRasterBand(1).SetNoDataValue(FillValue)
    grid.GetRasterBand(1).Fill(FillValue)

    # Setup projection and geo-transformation
    grid.SetProjection(targetPrj.ExportToWkt())
    grid.SetGeoTransform(getGeoT(extent, grid.RasterYSize, grid.RasterXSize))

    # Perform the projection/resampling
    gdal.ReprojectImage(raw, grid, sourcePrj.ExportToWkt(), targetPrj.ExportToWkt(), \
                        gdal.GRA_NearestNeighbour, options=options, \
                        callback=progress) #callback=gdal.TermProgress)
    # Close file
    raw = None

    # Read grid data
    array = grid.ReadAsArray()

    # Mask fill values (i.e. invalid values)
    array = np.ma.masked_equal(array, FillValue)

    # Apply scale and offset
    array = array * scale + offset

    # Fill-value
    array = np.ma.filled(array, FillValue)

    grid.GetRasterBand(1).SetNoDataValue(FillValue)
    grid.GetRasterBand(1).WriteArray(array)

    return grid
