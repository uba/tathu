#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import copy
from datetime import timedelta

from osgeo import ogr
from shapely import affinity, wkb

from tathu.tracking.forecasters import delta
from tathu.tracking.system import LifeCycleEvent

def ogr2shapely(geom):
    return wkb.loads(bytes(geom.ExportToWkb()))

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

def interpolate(start_system, end_system, step):
    elapsed_time = abs((start_system.timestamp - end_system.timestamp).total_seconds()/60)
    dx, dy = delta(start_system.geom.Centroid(), end_system.geom.Centroid(), elapsed_time)
    systems = []
    for t in range(1, int(elapsed_time), step):
        intepolated_system = copy.deepcopy(start_system)
        intepolated_system.event = LifeCycleEvent.INTERPOLATION
        intepolated_system.geom = translate(start_system.geom, -dx * t, -dy * t)
        intepolated_system.timestamp = start_system.timestamp + timedelta(minutes=t)
        systems.append(intepolated_system)
    return systems
