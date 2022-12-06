#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""
GOES-13 Downloader
==================

This is a general example demonstrating how download and view GOES-13 data from DISSM/INPE using TATHU support.
"""

import glob
from datetime import datetime

from osgeo import gdal

from tathu.constants import LAT_LONG_WGS84_BRAZIL_NORTH_EXTENT
from tathu.downloader.goes import DISSM
from tathu.progress import TqdmProgress
from tathu.satellite import goes13
from tathu.visualizer import MapView

### Setup Parameters ###

# Geographic area of regular grid
extent = LAT_LONG_WGS84_BRAZIL_NORTH_EXTENT

# Grid resolution (kilometers)
resolution = 4.0

# Data directory
dir = './goes13-dissm/'

# Download 08 April 2022, Channel 13, 00:xx UTC
start = end = datetime.strptime('20170408', '%Y%m%d')
hours = ['00']

# From DISSM (crop/remapped version - GOES-13)
DISSM.download('goes13', 'retangular_4km/ch4_bin',
    start, end, hours, dir,
    progress=TqdmProgress('Download GOES-13 data (DISSM)', 'files'))

# Search images
query = dir + '/**/*'

# Get files
files = sorted(glob.glob(query, recursive=True))

# Show first file
grid = goes13.sat2grid(files[0], extent, resolution, progress=gdal.TermProgress_nocb)

# Visualize result
m = MapView(extent)
m.plotImage(grid, cmap='Greys', vmin=180.0, vmax=320.0)
m.show()
