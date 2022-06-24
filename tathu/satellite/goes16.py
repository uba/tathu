#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import datetime

import numpy as np
import pyproj
from netCDF4 import Dataset
from osgeo import gdal, osr

from tathu.constants import KM_PER_DEGREE
from tathu.utils import getGeoT

# GOES-16 Spatial Reference System (proj4 string format)
G16Proj4 = '+proj=geos +h=35786023.0 +a=6378137.0 +b=6356752.31414 +f=0.00335281068119356027 +lat_0=0.0 +lon_0=-75.0 +sweep=x +no_defs'

# GOES-16 viewing point (satellite position) height above the earth
H = 35786023.0

# Full-disk (FD) properties by resolution (GOES-16)
G16FDNLinesDic = {'0.5' : 21696,    '1.0' : 10848,    '2.0' : 5424, '4.0' : 2712, '10.0' : 1086}
G16FDNColsDic  = {'0.5' : 21696,    '1.0' : 10848,    '2.0' : 5424, '4.0' : 2712, '10.0' : 1086}
G16FDScaleDic  = {'0.5' : 0.000014, '1.0' : 0.000028, '2.0' : 0.000056, '4.0' : 0.000112, '10.0' : 0.000280}
G16FDOffsetDic = {'0.5' : 0.151865, '1.0' : 0.151858, '2.0' : 0.151844, '4.0' : 0.151816, '10.0' : 0.151900}

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
    # Open GOES-16 netCDF file
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
    # Close GOES-16 netCDF file
    nc.close()
    return proj

def getProjExtent(path):
    nc = Dataset(path, mode='r')
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

def sat2grid(path, extent, resolution, targetPrj, driver='NETCDF', autoscale=False, progress=None, var='CMI'):
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

def getFullDiskInfos(res):
    return G16FDNLinesDic[res], G16FDNColsDic[res], G16FDScaleDic[res], G16FDOffsetDic[res]

def buildFullDiskLatLonGrid(resolution):
    # TODO: verify if resolution is valid.
    # Allowed values: ['0.5', '1.0', '2.0', '4.0', '10.0']

    # Get Full-disk properties
    nlines, ncols, scale, offset = getFullDiskInfos(resolution)

    # GOES-16 Spatial Reference System
    sourcePrj = pyproj.Proj(G16Proj4)

    # Lat/Lon WSG84 Spatial Reference System
    targetPrj = pyproj.Proj('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')

    # Create projection coordinates array
    x = np.arange(0, ncols)
    y = np.arange(0, nlines)

    # Apply scale and offset (scanning angle) + H factor = projection coordinates
    x = ((x * scale) - offset) * H
    y = ((y * (-1 * scale)) + offset) * H

    # Create matrix with values
    x, y = np.meshgrid(x, y)

    # Reshape to vector (1-d)
    x = x.reshape(nlines * ncols)
    y = y.reshape(nlines * ncols)

    # Transform
    lon, lat = pyproj.transform(sourcePrj, targetPrj, x, y)

    # Reshape to matrix format
    lat = lat.reshape(nlines, ncols)
    lon = lon.reshape(nlines, ncols)

    return lat, lon
