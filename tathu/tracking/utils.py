#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

from osgeo import gdal, ogr

from tathu.constants import KM_PER_DEGREE
from tathu.geometry.utils import extent2edges

def copyImage(image):
    driver = gdal.GetDriverByName('MEM')
    return driver.CreateCopy('image', image, 0)

def polygonize(image, minArea=None, progress=None):
    # Create layer in memory
    driver = ogr.GetDriverByName('MEMORY')
    ds = driver.CreateDataSource('systems')
    layer = ds.CreateLayer('geom', srs=None)

    # Get first band
    band = image.GetRasterBand(1)

    # Poligonize using GDAL method
    gdal.Polygonize(band, band.GetMaskBand(), layer, -1, options=['8CONNECTED=8'], callback=progress)

    polygons = []

    for feature in layer:
        # Get polygon representation (detail: using Buffer(0) to fix self-intersections)
        p = feature.GetGeometryRef().Buffer(0)
        # Verify minimum area
        if minArea is None:
            polygons.append(p)
        elif p.GetArea() > minArea:
            polygons.append(p)

    return polygons

def area2degrees(km2):
    return km2/(KM_PER_DEGREE * KM_PER_DEGREE)

def verify_edges(extent, systems):
    left, right, up, down = extent2edges(extent)
    for s in systems:
        for pos in ('left', 'right', 'up', 'down'):
            s.attrs['touching_' + pos] = False
        if s.geom.Intersects(left):
            s.attrs['touching_left'] = True
        if s.geom.Intersects(right):
            s.attrs['touching_right'] = True
        if s.geom.Intersects(up):
            s.attrs['touching_up'] = True
        if s.geom.Intersects(down):
            s.attrs['touching_down'] = True
