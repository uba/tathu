#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import copy
import math

from osgeo import ogr

from tathu.geometry import transform
from tathu.tracking.system import LifeCycleEvent

def compute_distance(p1, p2):
    x = p1.GetX() - p2.GetX()
    y = p1.GetY() - p2.GetY()
    return math.sqrt(x * x + y * y)

def compute_elapsed_time(sys):
    if not sys.relationships:
        return 0.0
    return abs((sys.timestamp - sys.relationships[0].timestamp).seconds/60)

def delta(p1, p2, elapsed_time=1.0):
    return (p1.GetX() - p2.GetX())/elapsed_time, (p1.GetY() - p2.GetY())/elapsed_time

def compute_last_centroid(sys):
    if not sys.relationships:
        return None

    if len(sys.relationships) == 1:
        return sys.relationships[0].geom.Centroid()

    # Compute mean centroid
    x = sys.geom.Centroid().GetX(); y = sys.geom.Centroid().GetY()
    for r in sys.relationships:
        x = (x + r.geom.Centroid().GetX()) * 0.5
        y = (y + r.geom.Centroid().GetY()) * 0.5

    centroid = ogr.Geometry(ogr.wkbPoint)
    centroid.AddPoint(x, y)

    return centroid

def compute_scale_factor(sys, elapsed_time=1.0):
    if not sys.relationships:
        return 0.0

    current_area = sys.geom.GetArea()

    previous_area = 0.0
    for r in sys.relationships:
        previous_area += r.geom.GetArea() 

    return ((current_area - previous_area)/previous_area)/elapsed_time

class Conservative(object):
    '''
    This class implements a conservative forecaster.
    '''
    def __init__(self, previous, intervals, applyScale=False):
        self.previous = previous # Set of previous systems at time.
        self.intervals = intervals # List of intervals for forecasting. Ex.: [15, 30, 45, 60] # minutes
        self.applyScale = applyScale # A flag that indicates if forecast will be scaled.

    def forecast(self, current):
        # Create results
        forecasts = {}
        for t in self.intervals:
            forecasts[t] = []

        # Perform forecasting
        for sys in current:
            if sys.event == LifeCycleEvent.SPONTANEOUS_GENERATION or sys.event == LifeCycleEvent.SPLIT:
                continue # no forecast, for while

            elapsedtime = compute_elapsed_time(sys)
            if elapsedtime == 0.0:
                continue

            ### Compute translation factor ###
            # Define last centroid (i.e.: at past)
            base = compute_last_centroid(sys)
            # Compute factor
            dx, dy = delta(sys.geom.Centroid(), base, elapsedtime)

            ### Compute scale factor ###
            scale = compute_scale_factor(sys, elapsedtime)

            # Apply transform (for each interval)
            for t in self.intervals:
                prevision = copy.deepcopy(sys)
                prevision.geom = transform.translate(sys.geom, dx * t, dy * t)
                if self.applyScale:
                    prevision.geom = transform.scale(prevision.geom, 1 + scale * t, 1 + scale * t)
                forecasts[t].append(prevision)

        return forecasts
