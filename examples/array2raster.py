#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""

import matplotlib.pyplot as plt
import numpy as np

from tathu.utils import array2raster

# Define geo extent
extent = [-100.0, -56.0, -20.0, 15.0]

# Create data
array = np.random.randint(0, 255, size=(1024, 1024))

# Convert to GDAL Dataset in memory
mem = array2raster(array, extent)

# Convert to GDAL Dataset file (geotiff)
#gtiff = array2raster(array, extent, output='raster.tif', driver='GTiff')

# Verify conversion
plt.imshow(array - mem.ReadAsArray(), cmap='gray')
plt.show()
