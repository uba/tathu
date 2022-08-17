#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""

import geopandas
import matplotlib.pyplot as plt
import pandas as pd
from osgeo import gdal

from tathu.geometry.transform import ogr2shapely
from tathu.satellite import goes13
from tathu.tracking import descriptors, detectors
from tathu.tracking.utils import area2degrees
from tathu.utils import file2timestamp

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

def systems2geopandas(systems):
    # Create dataframe with fixed attributes
    df = pd.DataFrame({
        'name': [str(s.name) for s in systems],
        'timestamp': [s.timestamp for s in systems],
        'event': [str(s.event) for s in systems]
    })
    # Add dynamic attributes
    for attr in systems[0].attrs:
        df[attr] = [s.attrs[attr] for s in systems]
        
    # Add geometry
    df['geom'] = [ogr2shapely(s.geom) for s in systems]

    # Creat geo-dataframe
    gdf = geopandas.GeoDataFrame(df, geometry='geom')

    # Adjust SRS
    gdf = gdf.set_crs('epsg:4326')

    return gdf

# Define images that will be used
img = '../data/goes13-dissm/S10236964_201704080000.gz'

# Detect systems
systems = detect(img)

# Convert result to geopandas dataframe
gdf = systems2geopandas(systems)
print(gdf.head())

# Export dataframe to geo-package
gdf.to_file('systems.gpkg', driver='GPKG', layer='systems')

# Show result
gdf.plot(figsize=(5, 5), alpha=0.5, edgecolor='k')
plt.show()
