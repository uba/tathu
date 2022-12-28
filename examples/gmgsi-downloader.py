#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""

import glob
from datetime import datetime

import matplotlib.animation as animation
import matplotlib.pyplot as plt
from netCDF4 import Dataset

from tathu.downloader.gmgsi import AWS
from tathu.progress import TqdmProgress

print('Available Products', AWS.getProducts())

# Download 05 December 2022, Channel IR, [00-08] hours UTC
start = end = datetime.strptime('20221206', '%Y%m%d')
hours = ['00', '01', '02', '03', '04', '05', '06', '07', '08']

# Define output directory
output_dir = './gmgsi-aws'

# From AWS (full-disk)
AWS.download(['GMGSI_LW'], start, end, hours, output_dir,
    progress=TqdmProgress('Download GMGSI data', 'files'))

 # Search download images
query = output_dir + '/**/*nc*'
print(query)

# Get files
files = sorted(glob.glob(query, recursive=True))

# Read arrays
arrays = []
for f in files:
    nc = Dataset(f)
    arrays.append(nc.variables['data'][:][0,:,:])
    nc.close()

# Show images
fig = plt.figure()
im = plt.imshow(arrays[0], cmap='gray')
plt.colorbar()

def animate(i):
    im.set_array(arrays[i])
    return [im]

fps = 30
anim = animation.FuncAnimation(fig, animate,
    frames=len(arrays), interval=1000/fps)

plt.show()
