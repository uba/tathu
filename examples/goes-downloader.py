#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""

from datetime import datetime

from tathu.downloader.goes import AWS, DISSM
from tathu.progress import TqdmProgress

# Download 08 April 2022, Channel 13, [00, 01, 02, 03] hours UTC
start = end = datetime.strptime('20220408', '%Y%m%d')
hours = ['00', '01', '02', '03']

# From AWS (full-disk)
AWS.download(AWS.buckets['GOES-16'], ['ABI-L2-CMIPF'],
    start, end, hours, ['13'], './goes16-aws',
    progress=TqdmProgress('Download GOES data (AWS)', 'files'))

# From DISSM (crop/remapped version)
hours = ['00', '01', '02', '03']
DISSM.download('goes16', 'retangular/ch13',
    start, end, hours,
    './goes16-dissm/',
    progress=TqdmProgress('Download GOES data (DISSM)', 'files'))
