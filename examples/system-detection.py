#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""

import sys

# To use local package
sys.path.append('../')

from osgeo import gdal

from tathu.constants import LAT_LON_WGS84
from tathu.io import icsv, vector
from tathu.satellite import goes16
from tathu.tracking import descriptors, detectors
from tathu.tracking.utils import area2degrees
from tathu.utils import file2timestamp
from tathu.visualizer import MapView

# Geographic area of regular grid
extent = [-100.0, -56.0, -20.0, 15.0]

def buildGrid(path):
    # Grid resolution (kilometers)
    resolution = 2.0
    print('Remapping')
    return goes16.sat2grid(path, extent, resolution, LAT_LON_WGS84, 'HDF5', progress=gdal.TermProgress_nocb)

# Path to netCDF GOES-16 file (IR-window)
path = '../data/OR_ABI-L2-CMIPF-M6C13_G16_s20221750000204_e20221750009523_c20221750010006.nc'

# Remap and get regular grid
grid = buildGrid(path)

# Threshold value
threshold = 230 # Kelvin
    
# Define minimum area
minarea = 3000 # km^2

# Convert to degrees^2
minarea = area2degrees(minarea)

# Create detector
detector = detectors.LessThan(threshold, minarea)

print('Searching for systems...')
systems = detector.detect(grid)
print('done.')

# Extract timestamp
timestamp = file2timestamp(path, regex=goes16.DATE_REGEX, format=goes16.DATE_FORMAT)
print('Date', timestamp)

 # Adjust timestamp
for s in systems:
    s.timestamp = timestamp

# Create statistical descriptor
descriptor = descriptors.StatisticalDescriptor()

print('Extracting systems attributes...')
# Describe systems (stats)
descriptor.describe(grid, systems)
print('done.')

print('Exporting result to csv file...')
outputter = icsv.Outputter('systems.csv', writeHeader=True, delimiter=',')
outputter.output(systems)
print('done.')

print('Exporting result to ESRI Shapefile...')
outputter = vector.Shapefile('systems.shp')
outputter.output(systems)
print('done.')

print('Exporting result to GeoJSON..')
outputter = vector.GeoJSON('systems.json')
outputter.output(systems)
print('done.')

print('Preparing result visualization...')

# Extract polygons
p = []
for s in systems:
    p.append(s.geom)

# Visualize result
m = MapView(extent)
m.plotImage(grid, cmap='Greys', vmin=180.0, vmax=320.0)
m.plotPolygons(p, facecolor='none', edgecolor='red', centroids=True)
m.show()
