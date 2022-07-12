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
from tathu.satellite import goes16
from tathu.tracking import descriptors, detectors, trackers
from tathu.tracking.utils import area2degrees
from tathu.utils import file2timestamp

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

# Attributes that will be computed (nae is normalized area expansion)
attrs = ['min', 'mean', 'std', 'count', 'nae']

def detect(path):
    # Extract timestamp
    timestamp = file2timestamp(path, regex=goes16.DATE_REGEX, format=goes16.DATE_FORMAT)
    
    print('Processing', timestamp)
    
    # Remap channel to 2km
    grid = goes16.sat2grid(path, extent, resolution, LAT_LON_WGS84,
        'HDF5', progress=gdal.TermProgress_nocb)
    
    # Create detector
    detector = detectors.LessThan(threshold, minarea)
    
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
    images = '../data/noaa-goes16/**/*.nc'

    # Get files
    files = sorted(glob.glob(images, recursive=True))

    # Detect first systems
    current = detect(files[0])

    # Create database connection
    db = spatialite.Outputter('systems-db.sqlite', 'systems', attrs)

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
        
        # Save to database
        db.output(current)
        
        # Prepare next iteration
        previous = current
    
    print('Done!')

if __name__ == "__main__":
    main()
