
#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""
Geometry Analysis
=================

This is a general example demonstrating how use set operations (e.g. ``Intersection``) for analyzing geometry objects.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from osgeo import ogr

def plot(geoms):
    plt.figure()
    for g in geoms:
        y = []; x = []
        points = g.GetGeometryRef(0).GetPoints()
        for p in points:
            y.append(p[0]); x.append(p[1])
        plt.plot(x, y, '.-')
        xy = list(zip(x, y))
        poly = Polygon(xy, facecolor='gray', alpha=0.4)
        plt.gca().add_patch(poly)
    plt.show()

p1 = ogr.CreateGeometryFromWkt('POLYGON((0.03217503217503248 0.12226512226512232, -0.11969111969111945 0.0141570141570142, 0.0141570141570142 -0.15572715572715579, 0.17374517374517406 -0.14543114543114544, 0.28185328185328196 -0.01158301158301156, 0.18404118404118419 0.14543114543114544, 0.18404118404118419 0.14543114543114544, 0.03217503217503248 0.12226512226512232))')

p2 = ogr.CreateGeometryFromWkt('POLYGON((0.38223938223938259 0.16087516087516085, 0.16859716859716878 0.08108108108108114, 0.11969111969111967 0.01673101673101673, 0.16602316602316636 -0.04504504504504503, 0.09395109395109413 -0.10167310167310162, 0.30501930501930508 -0.24066924066924056, 0.50321750321750347 -0.16602316602316591, 0.57271557271557283 0.02445302445302444, 0.48262548262548277 0.03732303732303732, 0.49549549549549576 0.11196911196911197, 0.38223938223938259 0.16087516087516085))')

intersection = p1.Intersection(p2)

print('P1 Area:', p1.GetArea())
print('P2 Area:', p2.GetArea())
print('Intersection Area:', intersection.GetArea())
print('%', intersection.GetArea()/p2.GetArea())

plot([p1, p2, intersection])
