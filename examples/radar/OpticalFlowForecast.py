#!/usr/bin/env python

import os
import sys
import datetime
import glob
import numpy as np

# Matplotlib Tools
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Polygon, Circle, Wedge

# Cartopy tools
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import cartopy.feature as cf
from osgeo import osr
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

# To use local package
sys.path.append('../../../tathu')

from tathu.tracking import trackers, descriptors, detectors, forecasters
from tathu.radar import radar
from tathu.tracking.utils import area2degrees
from tathu.geometry.utils import extractCoordinates2NumpyArray

paths = sorted(glob.glob('../../data/radar/cappi_CZ*'))

# Radar extent and dimensions
extent = [-50.3701, -18.2131, -45.6527, -13.7188]
nlines, ncols = 500, 500
nodata = -99.0

threshold = 20 #dBz
minarea = 9    # km2
minarea = area2degrees(minarea)
overlap=0.01
attrs=['min', 'mean', 'std', 'count']
intervals = [10, 20, 30]

def file2timestamp(path):
    sep=str.split(os.path.basename(path), '_')[3:]
    time_str = sep[0]+sep[1][0:4]
    return datetime.datetime.strptime(time_str, '%Y%m%d%H%M')

def detect(path):
    # Time definitions
    timestamp=file2timestamp(path)
    print('>> Processing: ', timestamp)

    # Get grid
    grid = radar.read(path, extent, nlines, ncols)

    # Operator definitions
    detector = detectors.GreaterThanOrEqualTo(threshold, minarea)
    systems  = detector.detect(grid)

    for s in systems:
        s.timestamp = timestamp
        
    descriptor = descriptors.StatisticalDescriptor(rasterOut=True)
    descriptor.describe(grid, systems)

    return systems, grid

# Get previous systems and grid
previous, gridP = detect(paths[0])

for path in paths[1:]:
    # Time
    timestamp = file2timestamp(path)
    
    # Searching for current systems
    current, gridC  = detect(path)

    # Tracking...
    strategy = trackers.AbsoluteOverlapAreaStrategy(overlap)
    t        = trackers.OverlapAreaTracker(previous, strategy=strategy)
    t.track(current)
    
    # Let's Prevision (Using Optical Flow Method)
    f=forecasters.ConservativeMergeSystemsOF(previous, intervals, gridP, gridC)
    forecasts = f.forecast(current)

    # Visualize
    proj = ccrs.PlateCarree()
    fig = plt.figure(1, frameon='False', figsize=(10, 8))
    ax = plt.axes(projection=proj)
    new_extent= [extent[0], extent[2], extent[1], extent[3]]
    ax.set_extent(new_extent, proj)

    gl = ax.gridlines(draw_labels=True, alpha=0.2)
    gl.top_labels = gl.right_labels = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    ax.add_feature(cf.COASTLINE)
    ax.add_feature(cf.BORDERS)
    ax.add_feature(cf.STATES, alpha=.2)
    ax.set_title('{}'.format(timestamp.strftime('%Y/%m/%d - %H:%M')))

    # Plot forecast Systems
    for s in current:
        coords = extractCoordinates2NumpyArray(s.geom)
        lons  = coords[:, 0]
        lats   = coords[:, 1]
        xy     = list(zip(lons, lats))
        poly   = Polygon(xy, lw=.8, ls='-', edgecolor='b', facecolor='None', transform=proj)
        ax.add_patch(poly)

        #Plota Previsão
        for interval in intervals:
                f = forecasts[interval]
                for p in f:
                    # Extract lat/lon
                    coords = extractCoordinates2NumpyArray(p.geom)
                    lons, lats = coords[:, 0], coords[:, 1]
                    # Plot polygon
                    xy = list(zip(lons, lats))
                    poly = Polygon(xy, lw=.7, ls='-', edgecolor='r', facecolor='None', transform=proj)
                    ax.add_patch(poly)
    plt.pause(3)
    plt.clf()
    previous = current
    gridP = gridC



