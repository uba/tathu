#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""

import numpy as np

from tathu.radar import radar
from tathu.tracking import detectors
from tathu.tracking.utils import area2degrees
from tathu.visualizer import MapView

# Radar extent and dimensions
extent = [-50.3701, -18.2131, -45.6527, -13.7188]
nlines, ncols = 500, 500
nodata = -99.0

# Path to data
path = '../data/radar/cappi_CZ_03000_20170930_1000.dat.gz'

# Read data
grid = radar.read(path, extent, nlines, ncols)

# Threshold value
threshold = 20 # DBZ

# Define minimum area
minarea = 10 # km^2
# Convert to degrees^2
minarea = area2degrees(minarea)

# Create detectors
detector = detectors.GreaterThan(threshold, minarea)

# Searching for systems
systems = detector.detect(grid)

# Get radar-values
array = grid.ReadAsArray()
array = np.ma.masked_where(array == nodata, array)

# Visualize result
m = MapView(extent)
m.plotArray(array, cmap='rainbow')
m.plotSystems(systems, facecolor='none', edgecolor='red', centroids=True)
m.show()
