#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

from collections import namedtuple
from datetime import datetime, timedelta

import numpy as np
from netCDF4 import Dataset
from osgeo import osr

from tathu.constants import KM_PER_DEGREE
from tathu.utils import array2raster, geo2grid, getGeoT

# Base date for compute product date-time (from www.goes-r.gov/users/docs/PUG-GRB-vol4.pdf)
basedate = datetime(2000, 1, 1, 12, 0, 0)

# Define Density type
Density = namedtuple('Density', ['timestamp', 'array'])

class LightningDensity(object):
    def __init__(self, files, extent, resolution, proj=None):
        self.files = files
        self.e = extent
        self.res = resolution

        self.proj = proj
        if proj is None:
            self.proj = osr.SpatialReference()
            self.proj.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')

        self.densities = []

        # Compute grid dimension
        self.nlines = int(((self.e[3] - self.e[1]) * KM_PER_DEGREE) / self.res)
        self.ncols = int(((self.e[2] - self.e[0]) * KM_PER_DEGREE) / self.res)

        # Compute geo-transform
        self.geoT = getGeoT(self.e, self.nlines, self.ncols)

    def build(self, interval):
        # Create grid
        density = np.zeros((self.nlines, self.ncols), dtype=np.uint32)

        # All densities
        self.densities = []

        # Dates for interval controlling
        basedate = None
        currentdate = None

        # For each GLM file
        for path in self.files:
            # Open file
            nc = Dataset(path, mode='r')

            # Define first basedate
            if basedate is None:
                basedate = self.__extractFileTime(nc)

            # Get current product date
            currentdate = self.__extractFileTime(nc)

            # Extract positions
            lats = nc.variables['flash_lat']
            lons = nc.variables['flash_lon']

            self.__remap2grid(density, lats[:], lons[:])

            nc.close()

            # Compute elapsed time
            delta = currentdate - basedate

            # Verify if interval is complete
            if delta.total_seconds() / 60.0 >= interval:
                print('Processed', basedate)
                # Store current density
                self.densities.append(Density(timestamp=basedate, array=np.copy(density)))
                # Update to next iteration
                basedate = currentdate
                density[:,:] = 0

        return self.densities

    def __remap2grid(self, density, lats, lons):
        # Get grid bounds
        nlines = density.shape[0]
        ncols = density.shape[1]
        # Remap
        lines, cols = self.__geo2grid(lons, lats)
        for i,j in zip(lines, cols):
            if i >= 0 and i < self.nlines and j >= 0 and j < self.ncols:
                density[i,j] += 1

    def __geo2grid(self, x, y):
        lin = (y - self.geoT[3]) / self.geoT[5]
        col = (x - self.geoT[0]) / self.geoT[1]
        return lin.astype(int), col.astype(int)

    def __extractFileTime(self, nc):
        sec = nc.variables['product_time'][0]
        time = basedate + timedelta(seconds=float(sec))
        return time

    def export(self, directory='./', prefix='den-'):
        for den in self.densities:
            # Build file name
            fname = directory + prefix + den.timestamp.strftime('%Y%m%d%H%M') + '.nc'
            # Create netCDF file
            nc = Dataset(fname, 'w', format='NETCDF4')
            x = nc.createDimension('x', den.array.shape[0])
            y = nc.createDimension('y', den.array.shape[1])
            density = nc.createVariable('density', np.uint32, ('x', 'y'))
            density[:] = den.array
            nc.close()

class NowcastingGLMDensity(object):
    def __init__(self, path):
        self.path = path

    def getExtent(self, path):
        nc = Dataset(self.path, mode='r')
        llx = min(nc.variables['lon'][:])
        lly = min(nc.variables['lat'][:])
        urx = max(nc.variables['lon'][:])
        ury = max(nc.variables['lat'][:])
        nc.close()
        return [llx, lly, urx, ury]

    def getData(self, var, extent=None):
        # Get full-extent (i.e. original from data)
        fullextent = self.getExtent(self.path)

        # Open file and extract data
        nc = Dataset(self.path, mode='r')
        array = nc.variables[var][0,:,:]
        array = np.flipud(array)

        # Get dimensions
        nlines = array.shape[0]
        ncols = array.shape[1]

        # Get geo-transform
        geoT = getGeoT(fullextent, nlines, ncols)

        if extent is not None:
            # Compute grid limits to cut data
            # From (upper-left corner)
            lini, coli = geo2grid(extent[0], extent[3], geoT)
            # From (lower-right corner)
            linf, colf = geo2grid(extent[2], extent[1], geoT)
            # Cut data
            array = array[lini:linf, coli:colf]
            # Adjust dimensions and geo-transform
            nlines = array.shape[0]
            ncols  = array.shape[1]
            geoT = getGeoT(extent, nlines, ncols)
        else:
            extent = fullextent

        nc.close()

        # Encapsulate using GDAL Dataset
        grid = array2raster(array, extent, nodata=0)

        return grid
