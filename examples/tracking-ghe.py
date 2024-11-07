#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""

import glob
import warnings

import shapely
from shapely.errors import ShapelyDeprecationWarning

import tathu.satellite.ghe as ghe
from tathu.io import spatialite
from tathu.tracking import descriptors, detectors, trackers
from tathu.tracking.utils import area2degrees
from tathu.utils import file2timestamp
from tathu.visualizer import MapView

# TODO: verify rasterstats package
warnings.filterwarnings('ignore', category=ShapelyDeprecationWarning)

# Threshold value
threshold = 2.0 # mm/h

# Define minimum area
minarea = 3000 # km^2

# Convert to degrees^2
minarea = area2degrees(minarea)

# Define overlap area criterion
overlapAreaCriterion = 0.1 # 10%

# Attributes that will be computed (nae is normalized area expansion)
attrs = ['min', 'mean', 'std', 'count', 'nae']

def detect(path):
    # Extract timestamp
    timestamp = file2timestamp(path, regex=ghe.DATE_REGEX, format=ghe.DATE_FORMAT)

    print('Processing GHE', timestamp)

    # Read GHE data
    grid = ghe.sat2grid(path)

    # Create detector
    detector = detectors.GreaterThan(threshold, minarea)

    # Searching for systems
    systems = detector.detect(grid)

    # Adjust timestamp
    for s in systems:
        s.timestamp = timestamp

    # Create statistical descriptor
    descriptor = descriptors.StatisticalDescriptor(rasterOut=True)

    # Describe systems (stats)
    descriptor.describe(grid, systems)

    for s in systems:
        s.attrs['nae'] = 0

    grid = None

    return systems

def main():
    # Base directory
    images = './data/NPR.GEO.GHE.v1.*.nc'

    # Get files
    files = sorted(glob.glob(images, recursive=True))

    # Detect first systems
    current = detect(files[0])

    # Create database connection
    db = spatialite.Outputter('GHE-db.sqlite', 'systems', attrs)

    # Save to database
    db.output(current)

    # Prepare tracking...
    previous = current

    # Create overlap area strategy
    strategy = trackers.RelativeOverlapAreaStrategy(overlapAreaCriterion)

    # for each image file
    for i in range(1, len(files)):
        # Detect current systems
        current = detect(files[i])

        # Let's track using Overlap Area
        t = trackers.OverlapAreaTracker(previous, strategy=strategy)
        t.track(current)

        # Let's track using Edge Topology
        t = trackers.EdgeTracker(previous)
        t.track(current)

        # Compute normalized area expansion attribute
        descriptor = descriptors.NormalizedAreaExpansionDescriptor()
        descriptor.describe(previous, current)

        # Save to database
        db.output(current)

        # Prepare next iteration
        previous = current

    print('Done!')

if __name__ == "__main__":
    main()
