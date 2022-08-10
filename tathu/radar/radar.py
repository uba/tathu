#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import os
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

# Dic of radars geospatial info
radars = {
    'R13537439': {
        'name': 'SaoRoque',
        'llx': -49.5786,
        'ury': -21.3379,
        'dx':  0.00995700,
        'dy': -0.00900140,
        'ncols': 500,
        'nlines': 500
    },
    'R13577441': {
        'name': 'Cangucu',
        'llx': -55.3873,
        'ury': -29.1325,
        'dx':  0.0107632,
        'dy': -0.00901620,
        'ncols': 500,
        'nlines': 500
    },
    'R13507440': {
        'name': 'Gama',
        'llx': -50.3701,
        'ury': -13.7188,
        'dx':  0.00943480,
        'dy': -0.00898860,
        'ncols': 500,
        'nlines': 500
    },
    'R12132246': {
        'name': 'PicoDoCouto',
        'llx': -45.7583,
        'ury': -20.2013,
        'dx':  0.00986420,
        'dy': -0.00899940,
        'ncols': 500,
        'nlines': 500
    },
    'R13557444': {
        'name': 'Santiago',
        'llx': -57.5513,
        'ury': -26.9560,
        'dx':  0.0105054,
        'dy': -0.00901180,
        'ncols': 500,
        'nlines': 500
    },
    'R12132246': {
        'name': 'MorroDaIgreja',
        'llx': -52.0632,
        'ury': -25.8599,
        'dx':  0.0103856,
        'dy': -0.00900980,
        'ncols': 500,
        'nlines': 500
    },
    'R12132246': {
        'name': 'Chapeco',
        'llx': -55.1672,
        'ury': -24.7816,
        'dx':  0.0102743,
        'dy': -0.00900776,
        'ncols': 500,
        'nlines': 500
    }
}

# Compute extent for each radar
for key in radars:
    sensor = radars[key]
    sensor['extent'] = [
        sensor['llx'],
        sensor['ury'] + sensor['dy'] * (sensor['nlines']),
        sensor['llx'] + sensor['dx'] * (sensor['ncols']),
        sensor['ury']
    ]

def getGeoSpatialInfo(path):
    filename = os.path.basename(path)
    preffix = filename.split('_')[0]
    return radars[preffix]
