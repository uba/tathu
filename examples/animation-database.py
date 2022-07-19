#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import glob
from tathu.constants import LAT_LONG_WGS84_BRAZIL_NORTH_EXTENT
from tathu.io import spatialite
from tathu import visualizer
from tathu.satellite import goes13
from tathu.utils import file2timestamp

# Geographic area of regular grid
extent = LAT_LONG_WGS84_BRAZIL_NORTH_EXTENT

# Setup informations to load systems from database
dbname = 'systems-db.sqlite'
table = 'systems'

# Load family
db = spatialite.Loader(dbname, table)

# Data directory
dir = '../data/goes13-dissm/'

# Search images
query = dir + '\**\*'

# Get files
files = sorted(glob.glob(query, recursive=True))

# Load images
images, timestamps = [], []
for path in files:
    images.append(goes13.sat2grid(path, extent))
    timestamps.append(file2timestamp(path, regex=goes13.DATE_REGEX, format=goes13.DATE_FORMAT))

# Animation
view = visualizer.AnimationMapDatabase(db, extent, images, timestamps)

# Save animation to file?
saveAnimation = True

if saveAnimation:
    # Set up formatting for the movie files
    import matplotlib.animation as animation
    Writer = animation.writers['ffmpeg']
    writer = Writer(bitrate=-1)
    view.save('db-animation.mp4')

view.show()
