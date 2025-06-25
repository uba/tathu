#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import os
from itertools import chain

import re
import requests
import s3fs

from tathu.utils import generateListOfDays

class AWS(object):
    # Define S3 Buckets
    buckets = {'GOES-16': 'noaa-goes16/', 'GOES-17': 'noaa-goes17/', 'GOES-18': 'noaa-goes18/', 'GOES-19': 'noaa-goes19/'}

    @staticmethod
    def isChannelSeparated(product):
        '''This function verifies if the given product is separeted by channels.'''
        return 'L1b-Rad' in product or 'L2-CMI' in product

    @staticmethod
    def getProducts(bucket):
        # Connection with S3 GOES AWS file system
        fs = s3fs.S3FileSystem(anon=True)
        products = []
        for p in fs.ls(bucket):
            if p.find('.html') == -1 and p.find('.pdf') == -1:
                products.append(p.replace(bucket, ''))
        return products
        
    @staticmethod
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
            hasChannels = AWS.isChannelSeparated(product)
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
            if progress:
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

class DISSM(object):
    baseurl = 'http://ftp.cptec.inpe.br/goes'
    satellites = ['goes13', 'goes16']
    channels = {
        'goes13': [
            'retangular_1km/ch1_bin',
            'retangular_4km/ch1_bin',
            'retangular_4km/ch2_bin',
            'retangular_4km/ch3_bin',
            'retangular_4km/ch4_bin',
            'retangular_4km/ch5_bin'
        ],
        'goes16': []
    }
    # Build channel names (i.e. ['01', '02, '03', ..., '15', '16'])
    channels['goes16'] = ['retangular/ch' + str(i).zfill(2) for i in range(1, 17)]

    @staticmethod
    def download(satellite, channel, start, end, hours, output, progress=None):
        # NOTE: using requests and RE because the CPTEC/FTP server is not currently accepting connection (?).
        # ftp = FTP('ftp.cptec.inpe.br') 
        # ftp.login() <== error!
        assert(satellite in DISSM.satellites)
        assert(channel in DISSM.channels[satellite])
        files = []
        # for each day
        for day in generateListOfDays(start, end):
            url = '{}/{}/{}/{}/{}'.format(DISSM.baseurl, satellite, channel,
                day.strftime('%Y'), day.strftime('%m'))
            resp = requests.get(url)
            day_files = re.findall('href="(.*.nc|.*.gz)"', resp.text)
            for hour in hours:
                regex = '.*_{}{}.*'.format(day.strftime('%Y%m%d'), hour)
                r = re.compile(regex)
                files.append(list(filter(r.match, day_files)))
        
        # Flat list of files
        files = list(chain.from_iterable(files))

        # Communicate number of files
        if progress:
            progress.startTask(len(files))

        # Download each file
        for f in files:
            if progress and progress.wasCanceled():
                break
            if progress:
                progress.startStep(f)

            # Build local file path
            local = os.path.join(output, f)
            if os.path.exists(local):
                progress.endStep(local)
                continue

            # Create local directory, if necessary
            os.makedirs(os.path.dirname(local), exist_ok=True)

            # Build url with file name
            url = '{}/{}/{}/{}/{}/{}'.format(DISSM.baseurl, satellite, channel,
                day.strftime('%Y'), day.strftime('%m'), f)

            # Download file!
            r = requests.get(url, allow_redirects=True)
            open(local, 'wb').write(r.content)

            # Notify
            if progress:
                progress.endStep(local)

        if progress:
            progress.endTask()
