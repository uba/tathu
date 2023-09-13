#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

'''
Downloader for NCEP/CPC 4km Global (60N - 60S) IR Dataset.
README: http://www.cpc.ncep.noaa.gov/products/global_precip/html/README
The data contain globally-merged (60S-60N) 4-km pixel-resolution IR brightness temperature
data (equivalent blackbody temperatures), merged from the European, Japanese, and U.S.
geostationary satellites over the period of record (GOES-8/9/10/11/12/13/14/15/16,
METEOSAT-5/7/8/9/10, and GMS-5/MTSat-1R/2/Himawari-8).
Every netCDF-4 file covers one hour, and contains two half-hourly grids, at 4-km grid cell resolution.
'''

import os
import platform
import shutil
from datetime import datetime, timedelta
from getpass import getpass
from subprocess import Popen

import requests

from tathu.utils import generateListOfDays

def create_prerequisite_files():
    '''
    Source: https://disc.gsfc.nasa.gov/information/howto?title=How%20to%20Generate%20Earthdata%20Prerequisite%20Files
    '''
    urs = 'urs.earthdata.nasa.gov' # Earthdata URL to call for authentication
    prompts = [
        'Enter NASA Earthdata Login Username: ',
        'Enter NASA Earthdata Login Password: '
    ]

    homeDir = os.path.expanduser('~') + os.sep

    # .netrc
    with open(homeDir + '.netrc', 'w') as file:
        file.write('machine {} login {} password {}'.format(urs, getpass(prompt=prompts[0]), getpass(prompt=prompts[1])))
        file.close()

    # .urs_cookies
    with open(homeDir + '.urs_cookies', 'w') as file:
        file.write('')
        file.close()

    # .dodsrc
    with open(homeDir + '.dodsrc', 'w') as file:
        file.write('HTTP.COOKIEJAR={}.urs_cookies\n'.format(homeDir))
        file.write('HTTP.NETRC={}.netrc'.format(homeDir))
        file.close()

    print('Saved .netrc, .urs_cookies, and .dodsrc to:', homeDir)

    # Set appropriate permissions for Linux/macOS
    if platform.system() != 'Windows':
        Popen('chmod og-rw ~/.netrc', shell=True)
    else:
        # Copy dodsrc to working directory in Windows
        shutil.copy2(homeDir + '.dodsrc', os.getcwd())
        print('Copied .dodsrc to:', os.getcwd())

class Earthdata:
    # Base repo
    repository = 'https://disc2.gesdisc.eosdis.nasa.gov/data/MERGED_IR/GPM_MERGIR.1/'

    @staticmethod
    def downloadAll(output='./'):
        start = end = datetime.strptime('20000208', '%Y%m%d')
        end = datetime.strptime('20230621', '%Y%m%d')
        Earthdata.download(start, end, output)

    @staticmethod
    def download(start, end, output, progress=None):
        create_prerequisite_files()
        for day in generateListOfDays(start, end):
            for hour in range(0, 24):
                date = day + timedelta(hours=hour)
                filename = date.strftime('merg_%Y%m%d%H_4km-pixel.nc4')
                url = date.strftime('{}%Y/%j/{}').format(Earthdata.repository, filename)
                print('Downloading', url, '|', 'Save to ->', output + filename)
                Earthdata.__request(url, output + filename)

    @staticmethod
    def __request(url, output):
        r = requests.get(url, allow_redirects=True)
        open(output, 'wb').write(r.content)

Earthdata.downloadAll()
