#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""

import glob

from osgeo import gdal

from tathu.constants import LAT_LON_WGS84
from tathu.io import spatialite
from tathu.satellite import goes_r
from tathu.tracking import descriptors, detectors, trackers
from tathu.tracking.utils import area2degrees
from tathu.utils import file2timestamp

import warnings
from shapely.errors import ShapelyDeprecationWarning
warnings.filterwarnings('ignore', category=ShapelyDeprecationWarning)

### Setup Parameters ###

# Geographic area of regular grid
extent = [-100.0, -56.0, -20.0, 15.0]

# Grid resolution (kilometers)
resolution = 2.0

# Threshold value
threshold = 230 # Kelvin

# Define minimum area
minarea = 3000 # km^2

# Convert to degrees^2
minarea = area2degrees(minarea)

# Define overlap area criterion
overlapAreaCriterion = 0.1 # 10%

# Stats attributes that will be computed
attrs = ['min', 'mean', 'std', 'median', 'count']

# Additional movement attributes that will be computed after tracking
movement_attrs = ['nae', 'velocity', 'u', 'v', 'direction']

def detect(path):
    # Extract timestamp
    timestamp = file2timestamp(path, regex=goes_r.DATE_REGEX, format=goes_r.DATE_FORMAT)

    print('Processing', timestamp)

    # Remap channel to 2km
    grid = goes_r.sat2grid(path, extent, resolution, LAT_LON_WGS84,
        'HDF5', progress=gdal.TermProgress_nocb)

    # Create detector
    detector = detectors.LessThan(threshold, minarea)

    # Searching for systems
    systems = detector.detect(grid)

    # Adjust timestamp
    for s in systems:
        s.timestamp = timestamp

    # Create statistical descriptor
    descriptor = descriptors.StatisticalDescriptor(stats=attrs, rasterOut=True)

    # Describe systems (stats)
    descriptor.describe(grid, systems)

    # Add additional attributes (computed after the tracking operation)
    for s in systems:
        s.addAtributes(movement_attrs) # will be computed later

    grid = None

    return systems

def main():
    # Base directory
    images = './data/noaa-goes16/**/*.nc'

    # Get files
    files = sorted(glob.glob(images, recursive=True))

    # Detect first systems
    current = detect(files[0])

    # Create database connection
    db = spatialite.Outputter('systems-db.sqlite', 'systems', attrs + movement_attrs)

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

        # Let's track!
        t = trackers.OverlapAreaTracker(previous, strategy=strategy)
        t.track(current)

        # Compute normalized area expansion attribute
        descriptor = descriptors.NormalizedAreaExpansionDescriptor()
        descriptor.describe(previous, current)

        # Compute velocity and direction attributes
        descriptor = descriptors.MovementDescriptor()
        descriptor.describe(previous, current)

        # Save to database
        db.output(current)

        # Prepare next iteration
        previous = current

    print('Done!')

if __name__ == "__main__":
    main()
