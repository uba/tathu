#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import datetime

import numpy as np
from netCDF4 import Dataset
from osgeo import gdal, osr

from tathu.constants import KM_PER_DEGREE, LAT_LON_WGS84
from tathu.utils import array2raster, getExtent, getGeoT

# Date format (from ABI File Naming Conventions)
DATE_REGEX = '\d{14}'
DATE_FORMAT = '%Y%j%H%M%S%f'

def getScaleOffset(path, var='CMI'):
    nc = Dataset(path, mode='r')
    scale = nc.variables[var].scale_factor
    offset = nc.variables[var].add_offset
    nc.close()
    return scale, offset

def getFillValue(path, var='CMI'):
    nc = Dataset(path, mode='r')
    value = nc.variables[var]._FillValue
    nc.close()
    return value

def getProj(path):
    # Open GOES-R netCDF file
    nc = Dataset(path, mode='r')
    # Get GOES-R ABI fixed grid projection
    proj = nc['goes_imager_projection']
    # Extract parameters
    h = proj.perspective_point_height
    a = proj.semi_major_axis
    b = proj.semi_minor_axis
    inv = 1.0 / proj.inverse_flattening
    lat0 = proj.latitude_of_projection_origin
    lon0 = proj.longitude_of_projection_origin
    sweep = proj.sweep_angle_axis
    # Build proj4 string
    proj4 = ('+proj=geos +h={} +a={} +b={} +f={} +lat_0={} +lon_0={} +sweep={} +no_defs').format(h, a, b, inv, lat0, lon0, sweep)
    # Create projection object
    proj = osr.SpatialReference()
    proj.ImportFromProj4(proj4)
    # Close GOES-R netCDF file
    nc.close()
    return proj

def getProjExtent(path):
    nc = Dataset(path, mode='r')
    H = nc['goes_imager_projection'].perspective_point_height
    llx = nc.variables['x_image_bounds'][0] * H
    lly = nc.variables['y_image_bounds'][1] * H
    urx = nc.variables['x_image_bounds'][1] * H
    ury = nc.variables['y_image_bounds'][0] * H
    nc.close()
    return [llx, lly, urx, ury]

def getGeoExtent(path):
    nc = Dataset(path, mode='r')
    extent = nc.variables['geospatial_lat_lon_extent']
    llx = extent.geospatial_westbound_longitude
    lly = extent.geospatial_southbound_latitude
    urx = extent.geospatial_eastbound_longitude
    ury = extent.geospatial_northbound_latitude
    nc.close()
    return [llx, lly, urx, ury]

def getCoverageTime(path):
    nc = Dataset(path, mode='r')
    start = datetime.datetime.strptime(nc.time_coverage_start, '%Y-%m-%dT%H:%M:%S.%fZ')
    end = datetime.datetime.strptime(nc.time_coverage_end, '%Y-%m-%dT%H:%M:%S.%fZ')
    nc.close()
    return start, end

def sat2grid(path, extent, resolution, targetPrj, driver='NETCDF', autoscale=True, progress=None, var='CMI'):
    # Read scale/offset from file
    scale, offset = getScaleOffset(path, var)

    # Extract GOES projection extent
    goesProjExtent = getProjExtent(path)

    # GOES spatial reference system
    sourcePrj = getProj(path)

    # Fill value
    fillValue = getFillValue(path, var)

    # Get total extent, if necessary
    if extent is None:
        extent = getGeoExtent(path)

    # Build connection info based on given driver name
    if driver == 'NETCDF':
        connectionInfo = 'NETCDF:\"' + path + '\":' + var
    elif driver == 'HDF5':
        connectionInfo = 'HDF5:\"' + path + '\"://' + var
    else:
        raise ValueError('Invalid driver name. Options: NETCDF or HDF5')

    # Open NetCDF file (GOES data) using GDAL
    raw = gdal.Open(connectionInfo, gdal.GA_ReadOnly)

    # Setup projection and geo-transformation
    raw.SetProjection(sourcePrj.ExportToWkt())
    raw.SetGeoTransform(getGeoT(goesProjExtent, raw.RasterYSize, raw.RasterXSize))
    raw.GetRasterBand(1).SetNoDataValue(float(fillValue))

    # Compute grid dimension
    sizex = int(((extent[2] - extent[0]) * KM_PER_DEGREE)/resolution)
    sizey = int(((extent[3] - extent[1]) * KM_PER_DEGREE)/resolution)

    # Get memory driver
    memDriver = gdal.GetDriverByName('MEM')

    # Output data type and fill-value
    type = gdal.GDT_Float32
    if autoscale is False:
        type, fillValue = gdal.GDT_UInt16, 65535

    # Create grid
    grid = memDriver.Create('grid', sizex, sizey, 1, type)
    grid.GetRasterBand(1).SetNoDataValue(float(fillValue))
    grid.GetRasterBand(1).Fill(float(fillValue))

    # Setup projection and geo-transformation
    grid.SetProjection(targetPrj.ExportToWkt())
    grid.SetGeoTransform(getGeoT(extent, grid.RasterYSize, grid.RasterXSize))

    # Perform the projection/resampling
    gdal.ReprojectImage(raw, grid, sourcePrj.ExportToWkt(), targetPrj.ExportToWkt(), \
                        gdal.GRA_NearestNeighbour, options=['NUM_THREADS=ALL_CPUS'], \
                        callback=progress)
    # Close file
    raw = None

    if autoscale:
        # Read grid data
        array = grid.ReadAsArray()
        # Apply scale and offset
        array = np.ma.masked_equal(array, fillValue)
        array = array * scale + offset
        array = np.ma.filled(array, fillValue)
        # Back to raster
        grid.GetRasterBand(1).WriteArray(array)

    # Adjust metadata, if necessary
    if autoscale is False:
        grid.SetMetadata(['SCALE={}'.format(scale), 'OFFSET={}'.format(offset)])

    return grid

def rect2grid(path, extent=None, resolution=2, autoscale=True, progress=None):
    # Read file and values
    dataset = gdal.Open(path, gdal.GA_ReadOnly)
    dataset.GetGeoTransform()
    raster = dataset.GetRasterBand(1)
    array = raster.ReadAsArray()
    if autoscale:
        array = array/100.0
    fullExtent = getExtent(dataset.GetGeoTransform(), array.shape)
    if extent is None: # No remap requested
        return array2raster(array, fullExtent)

    # else, remap to given extent...
    # Get memory driver
    memDriver = gdal.GetDriverByName('MEM')

    # Raster info
    dtype = raster.DataType
    fillValue = raster.GetNoDataValue()
    if autoscale:
        dtype = gdal.GDT_Float32
        fillValue = np.finfo(np.float32).min

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
    gdal.ReprojectImage(dataset, remapped, LAT_LON_WGS84.ExportToWkt(),
        LAT_LON_WGS84.ExportToWkt(), gdal.GRA_NearestNeighbour,
        options=['NUM_THREADS=ALL_CPUS'], callback=progress)

    if autoscale:
        # Read remapped data
        array = remapped.ReadAsArray()
        # Apply scale
        array = np.ma.masked_equal(array, fillValue)
        array = array/100.0
        array = np.ma.filled(array, fillValue)
        # Back to raster
        remapped.GetRasterBand(1).WriteArray(array)

    # Close file
    dataset = None

    return remapped
