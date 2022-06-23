#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

from enum import Enum

import numpy as np
from osgeo import ogr
from scipy import ndimage
from skimage.feature import peak_local_max
from skimage.morphology import watershed

from tathu.tracking.system import ConvectiveSystem, ConvectiveSystemManager
from tathu.tracking.utils import copyImage, polygonize

class ThresholdOp(Enum):
    '''
    Enumeration that represents threshold operators.
    '''
    LESS_THAN = 0,                # Less than operator (<).
    LESS_THAN_OR_EQUAL_TO = 1,    # Less than or equal operator (<=).
    GREATER_THAN = 2,             # Greater than operator (>).
    GREATER_THAN_OR_EQUAL_TO  = 3 # Greater than or equal to operator (>=).

class ThresholdDetector(object):
    '''
    This class implements a convective system detector that uses thresholding operation.
    '''
    def __init__(self, value, op, minarea=None):
        self.value = value     # Threshold value used by the detector.
        self.op = op           # Threshold operator used by the detector.
        self.minarea = minarea # Minimum area used to define a convective system.

    def detect(self, image):
        # Get image data
        data = image.ReadAsArray()

        # Thresholding values
        # Note: by exclusion. i.e. keep values that obey the threshold restriction
        if(self.op is ThresholdOp.LESS_THAN):
            data[data >= self.value] = 0
        elif(self.op is ThresholdOp.LESS_THAN_OR_EQUAL_TO):
            data[data > self.value] = 0
        elif(self.op is ThresholdOp.GREATER_THAN):
            data[data <= self.value] = 0
        elif(self.op is ThresholdOp.GREATER_THAN_OR_EQUAL_TO):
            data[data < self.value] = 0

        # Verify no-data
        nodata = image.GetRasterBand(1).GetNoDataValue()

        if(nodata):
            data[data == nodata] = 0

        # Find connected components
        labeled, nObjects = ndimage.label(data)

        # Create Gdal dataset with labeled result in order to apply polygonize operation
        objects = copyImage(image)
        objects.GetRasterBand(1).SetNoDataValue(0)
        objects.GetRasterBand(1).WriteArray(labeled)
        objects.FlushCache()

        # Polygonize objects
        polygons = polygonize(objects, self.minarea)

        # Create list of convective systems from polygons
        systems = []
        for p in polygons:
            systems.append(ConvectiveSystem(p))

        return systems

class MultiThresholdDetector(object):
    '''
    This class implements a convective system detector that uses multi-thresholding operations.
    '''
    def __init__(self, thresholds, op, minareas=None):
        self.thresholds = thresholds   # Threshold values used by the detector.
        self.op = op                   # Threshold operator used by the detector.
        self.minareas = minareas       # Minimum areas used to define a convective system and layers.

    def detect(self, image):
        # Use first threshold as system base (e.g. 235k)
        baseT = self.thresholds[0]

        # Use threshold detector to define first systems
        detector = ThresholdDetector(baseT, self.op, self.minareas[0])

        # Detect base systems (e.g. 235k)
        systems = detector.detect(image)

        # For each threshold layer
        for i in range(1, len(self.thresholds)):

            # Get current threshold
            layerT = self.thresholds[i]

            # Use threshold detector to define layer
            detector = ThresholdDetector(layerT, self.op, self.minareas[i])

            # Detect systems layers (e.g. 220k, 210k, 200k)
            layers = detector.detect(image)

            # Indexing layers
            manager = ConvectiveSystemManager(layers)

            # For each system, associate the layer
            for sys in systems:

                # Get overlap cells
                overlapLayers = manager.getSystemsFromSystem(sys)

                if not overlapLayers:
                    continue

                # Build multi-polygon layers
                mgeom = ogr.Geometry(ogr.wkbMultiPolygon)

                for l in overlapLayers:
                    mgeom.AddGeometry(l.geom.Clone())

                # Associate layer with threshold used
                lmap = {str(layerT) : mgeom}

                # Add atribute to system
                sys.layers.update(lmap)

        return systems

class WatershedDetector(object):
    '''
    This class implements a convective system detector that uses an image processng method called watershed.
    '''
    def __init__(self, value, op, pickMinDistance, minarea=None):
        self.value = value # Threshold value used by the detector.
        self.op = op # Threshold operator used by the detector.
        self.pickMinDistance = pickMinDistance # Minimum distance used to define picks.
        self.minarea = minarea # Minimum area used to define a convective system.

    def detect(self, image):
        # Get image data
        data = image.ReadAsArray()

        # Thresholding values
        if(self.op is ThresholdOp.LESS_THAN):
            data[data > self.value ] = 0
        elif(self.op is ThresholdOp.LESS_THAN_OR_EQUAL_TO):
            data[data >= self.value] = 0
        elif(self.op is ThresholdOp.GREATER_THAN):
            data[data < self.value ] = 0
        elif(self.op is ThresholdOp.GREATER_THAN_OR_EQUAL_TO):
            data[data <= self.value] = 0

        # Verify no-data
        nodata = image.GetRasterBand(1).GetNoDataValue()

        if(nodata):
            data[data == nodata] = 0

        data[data != 0] = 1

        # Convert to uint8
        data = np.uint8(data)

        # Perform Euclidean Distance Transform (EDT)
        edt = ndimage.distance_transform_edt(data)

        # Find picks
        localMax = peak_local_max(edt, indices=False, min_distance=self.pickMinDistance, labels=data)

        markers = ndimage.label(localMax)[0]

        # Watershed!
        labels = watershed(-edt, markers, mask=data)

        # Create Gdal dataset with labeled result in order to apply polygonize operation
        objects = copyImage(image)
        objects.GetRasterBand(1).SetNoDataValue(0)
        objects.GetRasterBand(1).WriteArray(labels)
        objects.FlushCache()

        # Polygonize objects
        polygons = polygonize(objects, self.minarea)

        # Create list of convective systems from polygons
        systems = []
        for p in polygons:
            systems.append(ConvectiveSystem(p))

        return systems
