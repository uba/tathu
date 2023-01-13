#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""

from datetime import datetime
from osgeo import gdal

from tathu.constants import LAT_LON_WGS84
from tathu.downloader.goes import AWS
from tathu.satellite import goes16
from tathu.tracking import descriptors, detectors, trackers, forecasters
from tathu.tracking.utils import area2degrees
from tathu.utils import file2timestamp
from tathu.visualizer import MapView
from tathu.progress import TqdmProgress

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
    timestamp = file2timestamp(path, regex=goes16.DATE_REGEX, format=goes16.DATE_FORMAT)
    print('Date', timestamp)
    grid = goes16.sat2grid(path, extent, resolution, LAT_LON_WGS84, 'HDF5', progress=gdal.TermProgress_nocb)
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

    return grid, systems

# Download 13 January 2023, Channel 13, [00] hours UTC
start = end = datetime.strptime('20230113', '%Y%m%d')
hours = ['00']

# From AWS (full-disk)
AWS.download(AWS.buckets['GOES-16'], ['ABI-L2-CMIPF'],
    start, end, hours, ['13'], './goes16-aws',
    progress=TqdmProgress('Download GOES-16 data (AWS)', 'files'))

# Define images that will be used (00:00 and 00:10 UTC)
img1 = './goes16-aws/noaa-goes16/ABI-L2-CMIPF/2023/013/00/OR_ABI-L2-CMIPF-M6C13_G16_s20230130000205_e20230130009525_c20230130010006.nc'
img2 = './goes16-aws/noaa-goes16/ABI-L2-CMIPF/2023/013/00/OR_ABI-L2-CMIPF-M6C13_G16_s20230130010205_e20230130019528_c20230130019586.nc'

# Detect systems
img1, systems1 = detect(img1)
img2, systems2 = detect(img2)

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
#m.plotImage(img1, cmap='Greys')
m.plotSystems(systems1, facecolor='red', edgecolor='red', centroids=False)
m.plotSystems(systems2, facecolor='blue', edgecolor='blue', alpha=0.5, centroids=False)
for t in forecasts:
    m.plotSystems(forecasts[t], facecolor='green', edgecolor='green', alpha=0.2, centroids=False)
m.show()
