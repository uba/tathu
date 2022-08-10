#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import glob

import numpy as np

from tathu import visualizer
from tathu.io import spatialite
from tathu.radar import radar
from tathu.utils import file2timestamp

# Setup informations to load systems from database
dbname = 'systems-radar-db.sqlite'
table = 'systems'

# Load family
db = spatialite.Loader(dbname, table)

# Data directory
dir = '../../data/radar/sroque-case'

# Search images
query = dir + '\R*_*.raw'

# Get files
files = sorted(glob.glob(query))

# Radar no-data value
nodata = -99.0

# Load images
images, timestamps = [], []
for path in files:
    geo = radar.getGeoSpatialInfo(path)
    array = radar.read(path, geo['extent'], geo['nlines'], geo['ncols']).ReadAsArray()
    array = np.ma.masked_where(array == nodata, array)
    images.append(array)
    timestamps.append(file2timestamp(path, regex='\\d{12}', format='%Y%m%d%H%M'))

# Animation
view = visualizer.AnimationMapDatabase(db, geo['extent'], images, timestamps, cmap='rainbow')

# Save animation to file?
saveAnimation = True

if saveAnimation:
    # Set up formatting for the movie files
    import matplotlib.animation as animation
    Writer = animation.writers['ffmpeg']
    writer = Writer(bitrate=-1)
    view.save('radar-db-animation.mp4')

view.show()
