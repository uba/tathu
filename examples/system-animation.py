#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

from tathu.io import spatialite
from tathu import visualizer

# Setup informations to load systems from database
dbname = 'systems-db.sqlite'
table = 'systems'

# Load family
db = spatialite.Loader(dbname, table)

# Get systems
names = db.loadNames()

# Load first
family = db.load(names[0], ['min', 'mean', 'std', 'count'])

# Animation
view = visualizer.AnimationMap(family, ['min', 'mean'])
view.show()
