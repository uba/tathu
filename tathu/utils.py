#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import datetime
import os
import re
import time

import numpy as np
from osgeo import gdal, gdal_array
from scipy import ndimage as nd

from tathu.constants import LAT_LON_WGS84

def getGeoT(extent, nlines, ncols):
    '''
    This function computes the resolution based on data dimensions.
    '''
    resx = (extent[2] - extent[0]) / ncols
    resy = (extent[3] - extent[1]) / nlines
    return [extent[0], resx, 0, extent[3] , 0, -resy]

def geo2grid(x, y, geoT):
    '''
    This function returns the grid point associated to a spatial location.
    \param x The spatial x-coordiante.
    \param y The spatial y-coordiante.
    \param geoTransform A list of 6 coefficients describing an affine transformation to georeference a grid.
    \return The grid point line and column.
    '''
    lin = (y - geoT[3]) / geoT[5]
    col = (x - geoT[0]) / geoT[1]
    return int(lin), int(col)

def grid2geo(lin, col, geoT):
    '''
    This function returns the spatial location of a grid point.
    \param geoTransform A list of 6 coefficients describing an affine transformation to georeference a grid.
    \param col The grid point column.
    \param row The grid point row.
    \return The spatial location.
    '''
    x = col * geoT[1] + geoT[0]
    y = lin * geoT[5] + geoT[3]
    return x, y

def getExtent(gt, shape):
    '''
    This function returns the extent based on the given GDAL
    geo-transform parameters and dimensions.
    '''
    llx = gt[0]
    lly = gt[3] + ((shape[0]) * gt[5])
    urx = gt[0] + ((shape[1])  * gt[1])
    ury = gt[3]
    return (llx, lly, urx, ury)

def generateListOfDays(start, end):
    '''This function returns all-days between given two dates.'''
    delta = end - start
    return [start + datetime.timedelta(i) for i in range(delta.days + 1)]

def extractPeriods(files, timeout, regex='\d{12}', format='%Y%m%d%H%M'):
    previous_time = None; result = []; period = []
    for path in files:
        # Get current date/time
        current_time = file2timestamp(path, regex, format)

        # Initialize, if necessary
        if previous_time is None:
            previous_time = current_time

        # Compute elapsed time
        elapsed_time = current_time - previous_time

        if elapsed_time.seconds > timeout * 60:
            result.append(period)
            period = []
            previous_time = None
        else:
            period.append(path)
            previous_time = current_time

    result.append(period)

    return result

def file2timestamp(path, regex='\d{12}', format='%Y%m%d%H%M'):
    '''
    This function extracts timestamp based on the given full-path file.
    '''
    # Extract filename
    filename = os.path.basename(path)

    # Extract date strings
    dates_strings = re.findall(regex, filename)

    for s in dates_strings:
        # Build date object
        date = datetime.datetime.strptime(s, format)
        # Return now. Detail: considering first found date
        return date

def array2raster(array, extent, srs=LAT_LON_WGS84, nodata=None, output='', driver='MEM'):
    # Get array dimension and data type
    nlines = array.shape[0]
    ncols = array.shape[1]
    type = gdal_array.NumericTypeCodeToGDALTypeCode(array.dtype)

    # Adjust nodata values
    if nodata is not None and isinstance(array, np.ma.MaskedArray):
        array = np.ma.filled(array, nodata)

    # Create GDAL raster
    driver = gdal.GetDriverByName(driver)
    raster = driver.Create(output, ncols, nlines, 1, type)
    raster.SetGeoTransform(getGeoT(extent, nlines, ncols))

    # Adjust band and write
    band = raster.GetRasterBand(1)
    if nodata is not None:
        band.SetNoDataValue(float(nodata))
    band.WriteArray(array)

    # Adjust SRS
    if srs is not None:
        raster.SetProjection(srs.ExportToWkt())

    band.FlushCache()

    return raster

def getGeoInfoFromCTL(path):
    '''
    This function try extract grid geospatial information from a CTL file.
    Geospatial info = number of lines, columns and geo-extent.
    '''
    with open(path, 'r') as f:
        fileContent = f.readlines()
    # Infos that will be searched
    llx = lly = nlines = ncols = resx = resy = None
    # Parser
    for line in fileContent:
        if line.lower().startswith('xdef'):
            tokens = line.lower().split()
            assert tokens[2] == 'linear'
            ncols = int(tokens[1])
            llx = float(tokens[3])
            resx = float(tokens[4])
        elif line.lower().startswith('ydef'):
            tokens = line.lower().split()
            assert tokens[2] == 'linear'
            nlines = int(tokens[1])
            lly = float(tokens[3])
            resy = float(tokens[4])
    assert llx and lly
    assert nlines and ncols
    assert resx and resy
    # Comput extent
    extent = [llx, lly, llx + (ncols * resx), lly + (nlines * resy)]
    return nlines, ncols, extent

def writeFLO(flow, filename):
    """
    Write optical flow in Middlebury .flo format.
    """
    flow = flow.astype(np.float32)
    f = open(filename, 'wb')
    magic = np.array([202021.25], dtype=np.float32)
    (height, width) = flow.shape[0:2]
    w = np.array([width], dtype=np.int32)
    h = np.array([height], dtype=np.int32)
    magic.tofile(f)
    w.tofile(f)
    h.tofile(f)
    flow.tofile(f)
    f.close()

def readFLO(path):
    '''
    This function reads Optical Flow Middlebury files (.flo).
    '''
    f = open(path, 'rb')

    # Read magic number ("PIEH" in ASCII = float 202021.25)
    magic = np.fromfile(f, np.float32, count=1)

    if magic != 202021.25:
        raise Exception('Invalid .flo file')

    # Read width
    f.seek(4)
    w = int(np.fromfile(f, np.int32, count=1))

    # Read height
    f.seek(8)
    h = int(np.fromfile(f, np.int32, count=1))

    # Read (u,v) coordinates
    f.seek(12)
    data = np.fromfile(f, np.float32, count=w*h*2)

    # Close file (.flo)
    f.close()

    # Reshape data into 3D array (columns, rows, bands)
    dataM = np.resize(data, (h, w, 2))

    # Extract u and v coordinates
    u = dataM[:,:,0]
    v = dataM[:,:,1]

    return w,h,u,v

def fill(data, invalid=None):
    '''
    From: https://stackoverflow.com/questions/3662361/fill-in-missing-values-with-nearest-neighbour-in-python-numpy-masked-arrays
    Replace the value of invalid 'data' cells (indicated by 'invalid')
    by the value of the nearest valid data cell
    Input:
        data:    numpy array of any dimension
        invalid: a binary array of same shape as 'data'. True cells set where data
                 value should be replaced.
                 If None (default), use: invalid  = np.isnan(data)
    Output:
        Return a filled array.
    '''
    if invalid is None: invalid = np.isnan(data)
    ind = nd.distance_transform_edt(invalid, return_distances=False, return_indices=True)
    return data[tuple(ind)]

class Timer(object):
    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args):
        print('> Time:', time.time() - self.start, 'seconds')
