#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""

from osgeo import gdal

from tathu.satellite import goes13
from tathu.tracking import descriptors, detectors, trackers, forecasters
from tathu.tracking.utils import area2degrees
from tathu.utils import file2timestamp
from tathu.visualizer import MapView

# Geographic area of regular grid
extent = [-100.0, -56.0, -20.0, 15.0]

# Threshold value
threshold = 230 # Kelvin
    
# Define minimum area
minarea = 3000 # km^2

# Convert to degrees^2
minarea = area2degrees(minarea)

# Define overlap area criterion
overlapAreaCriterion = 0.1 # 10%

# Grid resolution (kilometers)
resolution = 4.0

def buildGrid(path):
    # Extract timestamp
    timestamp = file2timestamp(path, regex=goes13.DATE_REGEX, format=goes13.DATE_FORMAT)
    print('Date', timestamp)
    grid = goes13.sat2grid(path, extent, resolution, progress=gdal.TermProgress_nocb)
    return grid, timestamp

def detect(path):
    # Remap and get regular grid
    grid, timestamp = buildGrid(path)

    # Create detector
    detector = detectors.LessThan(threshold, minarea)

    print('Searching for systems...')
    systems = detector.detect(grid)
    print('done.')

    # Adjust timestamp
    for s in systems:
        s.timestamp = timestamp

    # Create statistical descriptor
    descriptor = descriptors.StatisticalDescriptor()

    print('Extracting systems attributes...')
    # Describe systems (stats)
    descriptor.describe(grid, systems)
    print('done.')

    return systems

# Define images that will be used
img1 = '../data/goes13-dissm/S10236964_201704081200.gz'
img2 = '../data/goes13-dissm/S10236964_201704081230.gz'

# Detect systems
systems1 = detect(img1)
systems2 = detect(img2)

# Create overlap area strategy
strategy = trackers.RelativeOverlapAreaStrategy(overlapAreaCriterion)

 # Tracking
t = trackers.OverlapAreaTracker(systems1, strategy=strategy)
t.track(systems2)

# Forecast
intervals = [30, 60, 90, 120]
f = forecasters.Conservative(systems1, intervals=intervals, applyScale=True)
forecasts = f.forecast(systems2)

print('Done!')

# Visualize results
m = MapView(extent)
m.plotSystems(systems1, facecolor='red', edgecolor='red', centroids=True)
m.plotSystems(systems2, facecolor='blue', edgecolor='blue', alpha=0.5, centroids=True)
for t in forecasts:
    m.plotSystems(forecasts[t], facecolor='green', edgecolor='green', alpha=0.2, centroids=True)
m.show()
