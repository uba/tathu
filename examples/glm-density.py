#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import glob
from datetime import datetime

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np

from tathu.downloader.goes import AWS
from tathu.progress import TqdmProgress
from tathu.satellite import glm

# Download 08 April 2022, 00:xx UTC
start = end = datetime.strptime('20220408', '%Y%m%d')
hours = ['00']

# From AWS (download GLM data)
AWS.download(AWS.buckets['GOES-16'], ['GLM-L2-LCFA'],
    start, end, hours, None, './goes16-aws',
    progress=TqdmProgress('Download GOES-16 GLM data (AWS)', 'files'))

# Base directory
images = './goes16-aws/**/*.nc'

# Get files
files = sorted(glob.glob(images, recursive=True))

# Geographic area of regular grid (Brazil Southeast Region)
extent = [-53.0, -25.50, -39.00, -13.50]

# Resolution
resolution = 8.0

# Compute densties for each 5 minute interval
density = glm.LightningDensity(files, extent, resolution)
results = density.build(interval=5) # minutes

# Export to netCDF files
density.export(directory='./', prefix='den-')

# Adjust for cartopy format
extent = [extent[0], extent[2], extent[1], extent[3]]

# Map SRS
crs = ccrs.PlateCarree()

# Show results
for r in results:
    ax = plt.axes(projection=crs)
    ax.set_extent(extent, crs=crs)
    ax.coastlines(linewidth=0.4, linestyle='solid', color='lightgray')
    ax.add_feature(cfeature.BORDERS, linewidth=0.4, linestyle='solid', color='lightgray')
    im = ax.imshow(np.ma.masked_where(r.array == 0, r.array), transform=crs, extent=extent)
    ax.set_title(('Timestamp: {}').format(str(r.timestamp)))
    plt.colorbar(im)
    plt.show()
