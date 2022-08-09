#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""


import glob

import cv2

from tathu.constants import LAT_LONG_WGS84_BRAZIL_NORTH_EXTENT
from tathu.satellite import goes13
from tathu.utils import file2timestamp, writeFLO

extent = LAT_LONG_WGS84_BRAZIL_NORTH_EXTENT

# Base directory
images = '../../data/goes13-dissm/*.gz'

# Get files
files = sorted(glob.glob(images))

previous = None

for i in range(len(files)):
    path = files[i]
    print('Processing', path)
    current = goes13.sat2grid(path, extent).ReadAsArray()
    if previous is None:
        previous = current
        continue
    flow = cv2.calcOpticalFlowFarneback(previous, current, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    timestamp = file2timestamp(path, regex=goes13.DATE_REGEX, format=goes13.DATE_FORMAT)
    writeFLO(flow, 'uv_{}.flo'.format(timestamp.strftime('%Y%m%d%H%M')))
    previous = current
