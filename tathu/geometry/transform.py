#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

from osgeo import ogr
from shapely import affinity, wkb

def ogr2shapely(geom):
    return wkb.loads(geom.ExportToWkb())

def shapely2ogr(geom):
    return ogr.CreateGeometryFromWkb(geom.wkb)

def rotate(geom, angle):
    gshp = ogr2shapely(geom)
    rotated = affinity.rotate(gshp, angle, origin='center')
    return shapely2ogr(rotated)

def translate(geom, x, y):
    gshp = ogr2shapely(geom)
    translated = affinity.translate(gshp, x, y)
    return shapely2ogr(translated)

def scale(geom, x, y):
    gshp = ogr2shapely(geom)
    scaled = affinity.scale(gshp, x, y, origin='center')
    return shapely2ogr(scaled)

def skew(geom, x, y):
    gshp = ogr2shapely(geom)
    skewed = affinity.skew(gshp, x, y, origin='center')
    return shapely2ogr(skewed)
