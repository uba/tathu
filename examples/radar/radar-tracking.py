#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""

import glob

from tathu.io import spatialite
from tathu.radar import radar
from tathu.tracking import descriptors, detectors, trackers
from tathu.tracking.utils import area2degrees
from tathu.utils import file2timestamp

### Setup Parameters ###

# Radar extent and dimensions
extent = [-50.3701, -18.2131, -45.6527, -13.7188]
nlines, ncols = 500, 500
nodata = -99.0

# Threshold value
threshold = 20 # DBZ

# Define minimum area
minarea = 10 # km^2

# Convert to degrees^2
minarea = area2degrees(minarea)

# Define overlap area criterion
overlapAreaCriterion = 0.1 # 10%

# Attributes that will be computed (nae is normalized area expansion)
attrs = ['min', 'mean', 'std', 'count', 'nae']

def detect(path):
    # Extract timestamp (cappi_CZ_03000_20170930_1000.dat.gz)
    timestamp = file2timestamp(path, regex='\\d{8}_\\d{4}', format='%Y%m%d_%H%M')
    
    print('Processing', timestamp)
    
    # Remap channel to 2km
    grid = radar.read(path, extent, nlines, ncols)
    
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
    # Data directory
    dir = '../data/radar/'

    # Search images
    query = dir + '/cappi*'

    # Get files
    files = sorted(glob.glob(query, recursive=True))

    # Detect first systems
    current = detect(files[0])

    # Create database connection
    db = spatialite.Outputter('systems-radar-db.sqlite', 'systems', attrs)

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
