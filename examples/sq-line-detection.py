#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""

from osgeo import gdal

from tathu.constants import LAT_LON_WGS84
from tathu.satellite import goes_r
from tathu.tracking import descriptors
from tathu.tracking import detectors
from tathu.tracking import squall_line
from tathu.tracking.utils import area2degrees
from tathu.utils import file2timestamp
from tathu.visualizer import MapView

# Geographic area of regular grid (AM)
extent = [-70.0, -10.0, -45.0, 5.0]

def buildGrid(path):
    # Grid resolution (kilometers)
    resolution = 2.0
    print('Remapping')
    return goes_r.sat2grid(path, extent, resolution, LAT_LON_WGS84,
        'HDF5', progress=gdal.TermProgress_nocb)

# Path to netCDF GOES-16 file (IR-window)
path = './data/squall-line/S10635312_202001160210.nc'

# Remap and get regular grid
grid = buildGrid(path)

# Threshold value
threshold = 230 # Kelvin

# Define minimum area
minarea = 2000 # km^2

# Convert to degrees^2
minarea = area2degrees(minarea)

# Create detector
detector = detectors.LessThan(threshold, minarea)

print('Searching for systems...')
systems = detector.detect(grid)
print('done.')

# Extract timestamp
timestamp = file2timestamp(path,
    regex='\d{12}',
    format='%Y%m%d%H%M'
)
print('Date', timestamp)

# Adjust timestamp
for s in systems:
    s.timestamp = timestamp

# Create statistical descriptor
descriptor = descriptors.StatisticalDescriptor(rasterOut=True)

# Describe systems (stats)
print('Extracting systems attributes...')
descriptor.describe(grid, systems)
print('done.')

# Squall line detection
print('Detecting squall lines...')
detector = squall_line.Detector(
    systems, min_distance=300.0, linearity_threshold=0.65, min_nsystems=3
)
squalllines = detector.detect(grid)
print('done.')

if len(squalllines) == 0:
    print('No squall line detected.')
    exit(0)

for sl in squalllines:
    print('Squall line with {} systems'.format(len(sl.systems)))
    print('Squall line with {} linearity score'.format(sl.linearity_score))

print('Preparing result visualization...')

def visualize_sq_line(squalllines):
    # Visualize result
    m = MapView(extent)
    m.plotImage(grid, cmap='Greys', vmin=180.0, vmax=320.0)
    for sl in squalllines:
        m.plotPolygons(sl.getPolygons(), facecolor='none', edgecolor='blue', centroids=True)
        m.plotPolygons([sl.line_bufferred], facecolor='none', edgecolor='green', centroids=False)
        m.plotPolygons([sl.axis_bufferred], facecolor='red', edgecolor='none', centroids=False)
        m.plotPolygons([sl.convex_hull], facecolor='none', edgecolor='yellow', centroids=False)
    m.show()

visualize_sq_line(squalllines)
