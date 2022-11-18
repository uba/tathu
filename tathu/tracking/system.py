#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import sys
import uuid
from enum import Enum

from rtree import index

from tathu.geometry.utils import convert2interleaved, fitEllipse

class LifeCycleEvent(Enum):
    '''
    Enumeration that represents the life cycle events of convective systems.
    '''
    SPONTANEOUS_GENERATION = 0
    NATURAL_DISSIPATION = 1
    CONTINUITY = 2
    SPLIT = 3
    MERGE = 4

    def __str__(self):
        return self.name

class ConvectiveSystem(object):
    '''
    This class represents a convective system.
    '''
    def __init__(self, geom):
        self.name = uuid.uuid4()
        self.geom = geom
        self.layers = {}
        self.attrs = {}
        self.event = LifeCycleEvent.SPONTANEOUS_GENERATION
        self.timestamp = None
        self.relationships = []
        self.raster = None
        self.nodata = None
        self.geotransform = None

    def getGeomWKT(self):
        return self.geom.ExportToWkt()

    def getCentroid(self):
        c = self.geom.Centroid()
        return (c.GetX(), c.GetY())

    def getMBR(self):
        '''
        This method get the extent from OGRGeometry encapsulated by system object.
        The retrieved extent is converted automatically to interleaved representation.
        '''
        return convert2interleaved(self.geom.GetEnvelope())

    def hasGeom(self):
        return self.geom != None

    def getRelationshipNames(self):
        names = []
        for r in self.relationships:
            if r.name != self.name:
                names.append(str(r.name))
        return names

    def getRelationshipNamesAsString(self, separator=' '):
        names = ''
        for r in self.relationships:
            if r.name != self.name:
                names += str(r.name) + separator
        if names != '':
            names = names[:-1] # remove last separator
        return names

    def getAttrNames(self):
        return list(self.attrs.keys())

    def getConvexHull(self):
        return self.geom.ConvexHull()

    def fitEllipse(self):
        return fitEllipse(self.geom)

class ConvectiveSystemFamily(object):
    '''
    This class represents a convective system family,
    i.e. the convective system spatio-temporal history.
    '''
    def __init__(self):
        # List of systems that composes the family
        self.systems = []
        # Timestamp index
        self.timeIndex = {}
        # Build a invalid extent
        self.__extent = [sys.float_info.max, sys.float_info.max,
                         -sys.float_info.max, -sys.float_info.max]

    def addSystem(self, system):
        self.systems.append(system)
        if system.hasGeom():
            self.__updateExtent(system.getMBR())
        self.timeIndex[system.timestamp] = system

    def getExtent(self):
        return self.__extent

    def getPolygons(self):
        p = [s.geom for s in self.systems]
        return p

    def getConvexHulls(self):
        p = [s.geom.ConvexHull() for s in self.systems]
        return p

    def getEllipses(self):
        p = [fitEllipse(s.geom) for s in self.systems]
        return p

    def getCentroids(self):
        c = [s.getCentroid() for s in self.systems]
        return c

    def getEvents(self):
        events = [s.event for s in self.systems]
        return events

    def getTimestamps(self):
        t = [s.timestamp for s in self.systems]
        return t

    def getAttribute(self, attr):
        values = [s.attrs[attr] for s in self.systems]
        return values

    def getRasters(self):
        rasters = [s.raster for s in self.systems]
        return rasters

    def hasSplitOrMerge(self):
        for sys in self.systems:
            if sys.event == str(LifeCycleEvent.MERGE) or sys.event == str(LifeCycleEvent.SPLIT):
                return True
        return False

    def __updateExtent(self, e):
        # Update llx
        self.__extent[0] = min(self.__extent[0], e[0])
         # Update lly
        self.__extent[1] = min(self.__extent[1], e[1])
        # Update urx
        self.__extent[2] = max(self.__extent[2], e[2])
        # Update ury
        self.__extent[3] = max(self.__extent[3], e[3])

class ConvectiveSystemManager(object):
    '''
    This class implements a manager for convective systems objects.
    '''
    def __init__(self, systems):
        self.systems = systems
        self.rtree = index.Index()
        self.__build()

    def getSystemsFromSystem(self, system):
        return self.getSystemsFromGeom(system.geom)

    def getSystemsFromGeom(self, geom):
        # Get geometry extent
        e = convert2interleaved(geom.GetEnvelope())
        # Retrieve candidates (using geometry MBR)
        candidates = self.getSystemsFromExtent(e)
        # Final result: i.e. refine candidates (using intersector operator)
        result = []
        for c in candidates:
            if geom.Intersects(c.geom):
                result.append(c)

        return result

    def getSystemsFromExtent(self, e):
        # Search r-tree index
        hits = list(self.rtree.intersection(e, objects='raw'))
        # Retrieve found systems
        result = []
        for i in hits:
            result.append(self.systems[i])

        return result

    def __build(self):
        i = 0
        # Indexing convective systems using r-tree
        for s in self.systems:
            self.rtree.insert(i, s.getMBR(), obj=i)
            i += 1
