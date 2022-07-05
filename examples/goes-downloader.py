#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""

from datetime import datetime

from tathu.downloader import goes
from tathu.progress import TqdmProgress

# List products
products = goes.getProducts(goes.BUCKETS['GOES-16'])
print('Products', *products, sep = '\n')

# Download 08 April 2022, Channel 13, [00, 01, 02, 03] hours UTC
start = end = datetime.strptime('20220408', '%Y%m%d')
hours = ['00', '01', '02', '03']
goes.download(goes.BUCKETS['GOES-16'], ['ABI-L2-CMIPF'], start, end,
    hours, ['13'], './', progress=TqdmProgress('Download GOES data', 'files'))
