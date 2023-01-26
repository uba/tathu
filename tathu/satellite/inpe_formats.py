#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

from osgeo import gdal
from tathu.utils import getExtent, array2raster


class Retangular:
    " Deal with INPE's  rectangular format"

    def __init__(self, filename: str):
        
        assert isinstance(filename, str), f" Can't load: Filename {filename} is not a string."
        
        self.dataset = gdal.Open(filename, gdal.GA_ReadOnly)
        self.geoTransform = self.dataset.GetGeoTransform()
        self.raster = self.dataset.GetRasterBand(1) 
        self.array = self.raster.ReadAsArray()/100
        self.shape = self.array.shape
        self.extent = list(getExtent(self.geoTransform, self.shape))

    def to_raster(self):
        
        return array2raster(self.array, self.extent)

