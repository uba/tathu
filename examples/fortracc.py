#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

from tathu.fortracc import Fortracc

f = Fortracc(threshold=235, resolution=2.0)
f.run('./data/noaa-goes16/**/*.nc')
