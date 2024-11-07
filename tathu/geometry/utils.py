#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import cv2
import numpy as np
from osgeo import ogr

def convert2interleaved(e):
    '''
    Auxiliary function that converts an extent to interleaved format
    i.e. [llx, urx, lly, ury] --> [llx, lly, urx, ury]
    '''
    return (e[0], e[2], e[1], e[3])

def extractCoordinates(polygon):
    '''
    This method extract the coordinates of polygon to two python lists.
    '''
    lats, lons = [], []
    points = polygon.GetGeometryRef(0).GetPoints()
    for p in points:
        lons.append(p[0]); lats.append(p[1])
    return lats, lons

def extractCoordinates2NumpyArray(polygon):
    '''
    This method extract the coordinates of polygon to NumpyArray (N x 2).
    '''
    points = polygon.GetGeometryRef(0).GetPoints()
    coords = np.zeros((len(points), 2), dtype=np.float32)
    i = 0
    for p in points:
        coords[i,0] = p[0]
        coords[i,1] = p[1]
        i += 1
    return coords

def extent2polygon(extent):
    '''
    This method converts the given extent to a polygon geometry object.
    '''
    # Create exterior ring
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint_2D(extent[0], extent[1])
    ring.AddPoint_2D(extent[2], extent[1])
    ring.AddPoint_2D(extent[2], extent[3])
    ring.AddPoint_2D(extent[0], extent[3])
    ring.AddPoint_2D(extent[0], extent[1])

    # Create polygon
    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)

    return polygon

def extent2edges(extent):
    '''
    This method converts the given extent to 4 lines that represent its edges.
    '''
    left = ogr.Geometry(ogr.wkbLineString)
    left.AddPoint_2D(extent[0], extent[1])
    left.AddPoint_2D(extent[0], extent[3])

    right = ogr.Geometry(ogr.wkbLineString)
    right.AddPoint_2D(extent[2], extent[1])
    right.AddPoint_2D(extent[2], extent[3])

    up = ogr.Geometry(ogr.wkbLineString)
    up.AddPoint_2D(extent[0], extent[3])
    up.AddPoint_2D(extent[2], extent[3])

    down = ogr.Geometry(ogr.wkbLineString)
    down.AddPoint_2D(extent[0], extent[1])
    down.AddPoint_2D(extent[2], extent[1])

    return left, right, up, down

def ellipse2polygon(x, y, ra, rb, ang, npoints=32):
    '''
    Create polygon based on given ellipse parameters.
    x0,y0 - position of centre of ellipse
    ra - major axis length
    rb - minor axis length
    ang - angle
    npoints - No. of points that make an ellipse

    Based on matlab code ellipse.m written by D.G. Long,
    Brigham Young University, based on the
    CIRCLES.m original
    written by Peter Blattner, Institute of Microtechnology,
    University of Neuchatel, Switzerland, blattner@imt.unine.ch
    '''
    xpos, ypos = x,y
    radm, radn= ra,rb
    an = ang

    co, si = np.cos(an),np.sin(an)
    the=np.linspace(0, 2 * np.pi, npoints)
    X=radm * np.cos(the) * co-si * radn * np.sin(the) + xpos
    Y=radm * np.cos(the) * si+co * radn * np.sin(the) +ypos

    # Create OGR Polygon
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for x, y in zip(X,Y):
        ring.AddPoint(x, y)

    p = ogr.Geometry(ogr.wkbPolygon)
    p.AddGeometry(ring)

    return p

def fitEllipse(polygon):
    # Extract coordinates to NumpyArray in order to user opencv2.fitEllipse
    coords = extractCoordinates2NumpyArray(polygon)

    # Fit ellipse
    (xc,yc), (a,b), theta = cv2.fitEllipse(coords)

    # Compute eccentricity
    major_ax, minor_ax = a, b
    if a < b: major_ax, minor_ax = b, a
    eccentricity = np.sqrt(1 - ((minor_ax * minor_ax)/(major_ax * major_ax)))
    
    return ellipse2polygon(xc, yc, a * 0.5, b * 0.5, -theta), eccentricity, theta


def getRadiusFromCircle(polygon):
    # Extract coordinates to NumpyArray in order to user opencv2.minEnclosingCircle
    coords = extractCoordinates2NumpyArray(polygon)

    # Fit Circle
    (x,y), radius = cv2.minEnclosingCircle(coords)

    return radius
