#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

'''
Downloader for NOAA Global Mosaic of Geostationary Satellite Imagery (GMGSI) Product.
NOAA/NESDIS Global Mosaic of Geostationary Satellite Imagery (GMGSI) visible (VIS), shortwave infrared (SIR),
longwave infrared (LIR) imagery, and water vaport imagery (WV) are composited from data from several geostationary
satellites orbiting the globe, including the GOES-East and GOES-West Satellites operated by U.S. NOAA/NESDIS, the
Meteosat-11 and Meteosat-8 satellites from theMeteosat Second Generation (MSG) series of satellites operated by
European Organization for the Exploitation of Meteorological Satellites (EUMETSAT), and the Himawari-8 satellite
operated by the Japan Meteorological Agency (JMA).
Reference: https://registry.opendata.aws/noaa-gmgsi/
'''

from itertools import chain
import os
import s3fs
from tathu.utils import generateListOfDays

class AWS(object):
    # Define S3 Bucket
    bucket = 'noaa-gmgsi-pds/'

    @staticmethod
    def getProducts():
        # Connection with S3 GOES AWS file system
        fs = s3fs.S3FileSystem(anon=True)
        products = []
        for p in fs.ls(AWS.bucket):
            if p.find('.html') == -1:
                products.append(p.replace(AWS.bucket, ''))
        return products

    @staticmethod
    def download(products, start, end, hours, output, progress=None):
        # Connection with S3 GOES AWS file system
        fs = s3fs.S3FileSystem(anon=True)

        # Build list of days
        days = generateListOfDays(start, end)

        # Searching for files
        files = []
        for product in products:
            if AWS.bucket not in product:
                product = AWS.bucket + product
            for day in days:
                for hour in hours:
                    # search files by day/hour: <product/YYYY/MM/DD/HH*>
                    query = ('{}/{}/{}/{}/{}/*'.format(product,
                        day.strftime('%Y'), day.strftime('%m'), day.strftime('%d'), hour)
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
