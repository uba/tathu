#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np

from tathu.radar import radar

# Radar extent and dimensions
extent = [-50.3701, -18.2131, -45.6527, -13.7188]
nlines, ncols = 500, 500
nodata = -99.0

path = '../data/radar/cappi_CZ_03000_20170930_1000.dat.gz'
raster = radar.read(path, extent, nlines, ncols)

array = raster.ReadAsArray()
array = np.ma.masked_where(array == nodata, array)

extent = [extent[0], extent[2], extent[1], extent[3]]
crs = ccrs.PlateCarree()

ax = plt.axes(projection=crs)
ax.set_extent(extent, crs=crs)
ax.coastlines(linewidth=0.4, linestyle='solid', color='white')
ax.add_feature(cfeature.BORDERS, linewidth=0.4, linestyle='solid', color='white')
ax.gridlines(draw_labels=True, linewidth=0.25, linestyle='--', color='k')
ax.imshow(array, transform=crs, cmap='rainbow', extent=extent)

plt.show()
