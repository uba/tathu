#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import datetime
import os
from itertools import chain

import s3fs

# Define S3 Buckets
BUCKETS = {
    'GOES-16' : 'noaa-goes16/',
    'GOES-17' : 'noaa-goes17/'
}

def isChannelSeparated(product):
    '''This function verifies if the given product is separeted by channels.'''
    return 'L1b-Rad' in product or 'L2-CMI' in product

def generateListOfDays(start, end):
    '''This function returns all-days between given two dates.'''
    delta = end - start
    return [start + datetime.timedelta(i) for i in range(delta.days + 1)]

def download(bucket, products, start, end, hours, channels, output, progress=None):
    # Connection with S3 GOES AWS file system
    fs = s3fs.S3FileSystem(anon=True)

    # Build list of days
    days = generateListOfDays(start, end)

    # Searching for files
    files = []
    for product in products:
        if bucket not in product:
            product = bucket + product
        hasChannels = isChannelSeparated(product)
        for day in days:
            for hour in hours:
                if not hasChannels:
                    # search files by day/hour: <product/YYYY/J/HH/*>
                    query = ('{}/{}/{}/{}/*'.format(product,
                        day.strftime('%Y'), day.strftime('%j'), hour)
                    )
                    files.append(fs.glob(query))
                else:
                    for channel in channels:
                        # search files by day/hour/channel: <product/YYYY/J/HH/*>
                        query = ('{}/{}/{}/{}/*C{}*'.format(product,
                            day.strftime('%Y'), day.strftime('%j'), hour, channel)
                        )
                        files.append(fs.glob(query))

    # Flat list of files
    files = list(chain.from_iterable(files))

    # Communicate number of files
    if progress:
        progress.startTask(len(files))

    # Download each file
    for f in files:
        if progress and progress.wasCanceled():
            break
        progress.startStep(f)
        # Build local file path
        local = os.path.join(output, f)
        if os.path.exists(local):
            progress.endStep(local)
            continue

        # Create local directory, if necessary
        os.makedirs(os.path.dirname(local), exist_ok=True)

        # Download file!
        fs.get(f, local)

        # Notify
        if progress:
            progress.endStep(local)

    if progress:
        progress.endTask()

def getProducts(bucket):
    # Connection with S3 GOES AWS file system
    fs = s3fs.S3FileSystem(anon=True)
    products = []
    for p in fs.ls(bucket):
        if p.find('.html') == -1 and p.find('.pdf') == -1:
            products.append(p.replace(bucket, ''))
    return products
