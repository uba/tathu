#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import glob

from tathu.tracking.utils import area2degrees

from tathu.io import spatialite
from tathu.utils import file2timestamp
from tathu.satellite.glm import NowcastingGLMDensity
from tathu.tracking import descriptors
from tathu.tracking import detectors
from tathu.tracking import trackers
from tathu.visualizer import MapView

### Setup Parameters ###

# Define extent
extent = [-53.0, -26.0, -44.0, -19.0]

# Define stats
stats = ['max', 'mean', 'std', 'count']

# Threshold value
threshold = 1 # Number of lightnings (>=)

# Define minimum area
minarea =  16 # km^2

# Convert to degrees^2
minarea = area2degrees(minarea)

def view(systems, grid):
    # Visualize result
    m = MapView(extent)
    m.plotImage(grid)
    m.plotSystems(systems, facecolor='none', edgecolor='red', centroids=True)
    m.show()

def detect(path, var, visualize=False):
    # Extract timestamp
    timestamp = file2timestamp(path)

    print('*** Processing', timestamp, path, '***')

    # Get data
    glm = NowcastingGLMDensity(path) # from DIPTC/INPE
    grid = glm.getData(var, extent)

    # Create detector
    detector = detectors.GreaterThan(threshold, minarea)

    # Searching for systems
    systems = detector.detect(grid)

    # Adjust timestamp
    for s in systems:
        s.timestamp = timestamp

    # Create statistical descriptor
    descriptor = descriptors.StatisticalDescriptor(stats=stats, rasterOut=True)

    # Describe systems (stats)
    descriptor.describe(grid, systems)

    if visualize:
        view(systems, grid)

    grid = None

    return systems

def main():
    # Base directory
    images = '*.nc'

    # Get files
    files = sorted(glob.glob(images))

    # Define variable that will be tracked
    var = 'group' # or flash

    # Visualize results at run-time?
    visualize = False

    # Detect first systems
    current = detect(files[0], var, visualize)

    # Create database connection
    db = spatialite.Outputter('glm-tracking-' + var + '.sqlite', 'systems', stats)

    # Save to database
    db.output(current)

    # Prepare tracking...
    previous = current

    # Create overlap area strategy
    strategy = trackers.IntersectsStrategy()

    # for each image file
    for i in range(1, len(files)):
        # Detect current systems
        current = detect(files[i], var, visualize)

        # Let's track!
        t = trackers.OverlapAreaTracker(previous, strategy=strategy)
        t.track(current)

        # Save to database
        db.output(current)

        # Prepare next iteration
        previous = current

    print('Done!')

if __name__ == "__main__":
    main()
