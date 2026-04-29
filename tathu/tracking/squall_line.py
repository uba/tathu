#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import sys
import uuid

import numpy as np
from osgeo import ogr

from tathu.constants import KM_PER_DEGREE
from tathu.geometry.utils import fitEllipse

class SquallLine(object):
    '''
    This class represents a squall line, i.e. a family of convective systems
    that are linearly spatially connected.
    '''
    def __init__(self, systems):
        # Unique identifier
        self.name = uuid.uuid4()

        # List of systems that composes the squall line
        self.systems = systems

        # Build a invalid extent
        self.__extent = [sys.float_info.max, sys.float_info.max,
            -sys.float_info.max, -sys.float_info.max]

        # Compute squall line extent based on the systems that composes it
        self.__computeExtent()

        # Build line geometry based on the centroids of the systems
        self.line = ogr.Geometry(ogr.wkbLineString)
        for system in self.systems:
            # Get centroid
            centroid = system.geom.Centroid()
            # Add to Line
            self.line.AddPoint(centroid.GetX(), centroid.GetY())

        # Compute main axis
        self.axis = self.__computeAxis()

        # buffer of 0.1 degree (visualization purposes only)
        self.line_bufferred = self.line.Buffer(0.05)
        self.axis_bufferred = self.axis.Buffer(0.05)

        # Compute convex hull of the polygons that composes the squall line
        multipolygon = ogr.Geometry(ogr.wkbMultiPolygon)
        for s in self.systems:
            multipolygon.AddGeometry(s.geom)
        self.convex_hull = multipolygon.ConvexHull()

        # Fit ellipse to convex hull
        self.ellipse, self.eccentricity, self.theta = fitEllipse(self.convex_hull)

        # Compute linearity score
        self.linearity_score = self.linearity_score()

    def __computeAxis(self):
        # Collect centroid coordinates
        coords = []
        for system in self.systems:
            c = system.geom.Centroid()
            coords.append([c.GetX(), c.GetY()])
        coords = np.array(coords)
        # Compute mean
        mean = coords.mean(axis=0)
        # Center data
        centered = coords - mean
        # Covariance matrix
        cov = np.cov(centered.T)
        # Eigen decomposition
        eigvals, eigvecs = np.linalg.eig(cov)
        # Get principal direction (largest eigenvalue)
        principal_dir = eigvecs[:, np.argmax(eigvals)]
        # Project points onto principal direction
        projections = centered @ principal_dir
        min_proj = projections.min()
        max_proj = projections.max()
        # Compute endpoints
        p1 = mean + min_proj * principal_dir
        p2 = mean + max_proj * principal_dir
        # Create OGR line
        axis = ogr.Geometry(ogr.wkbLineString)
        axis.AddPoint(float(p1[0]), float(p1[1]))
        axis.AddPoint(float(p2[0]), float(p2[1]))
        return axis

    def getExtent(self):
        return self.__extent

    def getPolygons(self):
        p = [s.geom for s in self.systems]
        return p

    def getCentroids(self):
        c = [s.getCentroid() for s in self.systems]
        return c

    def getLine(self):
        return self.line

    def __computeExtent(self):
        for s in self.systems:
            if s.hasGeom():
                self.__updateExtent(s.getMBR())

    def __updateExtent(self, e):
        # Update llx
        self.__extent[0] = min(self.__extent[0], e[0])
         # Update lly
        self.__extent[1] = min(self.__extent[1], e[1])
        # Update urx
        self.__extent[2] = max(self.__extent[2], e[2])
        # Update ury
        self.__extent[3] = max(self.__extent[3], e[3])

    def structural_linearity(self):
        """
        Structural linearity index based on PCA.
        LI = 1 - (λ2 / λ1)
        λ1 = largest eigenvalue of the covariance matrix
        λ2 = smallest eigenvalue
        Returns a value between 0 and 1.
        """
        pts = np.array(self.line.GetPoints())[:, :2]
        if len(pts) < 3:
            return 1.0
        centered = pts - pts.mean(axis=0)
        cov = np.cov(centered.T)
        eigvals = np.linalg.eigvalsh(cov)
        eigvals = np.sort(eigvals)[::-1]
        l1, l2 = eigvals
        if l1 == 0:
            return 0.0
        return 1.0 - (l2/l1)

    def geometric_straightness(self):
        """
        Geometric straightness index.
        SI = D / L
        D = distance between the endpoints
        L = line length
        Returns a value between 0 and 1.
        """
        L = self.line.Length()
        if L == 0:
            return 0.0
        p0 = self.line.GetPoint(0)
        p1 = self.line.GetPoint(self.line.GetPointCount() - 1)
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        D = np.sqrt(dx * dx + dy * dy)
        return D / L

    def linearity_score(self):
        """
        Score = LI * SI
        """
        li = self.structural_linearity()
        si = self.geometric_straightness()
        return li * si

class Detector(object):
    '''
    This class implements a convective system detector that
    uses a simple method to define squall lines.
    '''
    def __init__(self, systems, min_distance, linearity_threshold, min_nsystems=2):
         # List of convective systems used by the detector.
        self.systems = systems

         # Minimum distance between systems to be considered part of the same squall line.
        self.min_distance = min_distance/KM_PER_DEGREE

        # Threshold for the linearity. e.g. > 0.8
        self.linearity_threshold = linearity_threshold

        # Minimum number of systems to be considered a squall line.
        self.min_nsystems = min_nsystems

    def detect(self, image):
        # List of squall lines that will be defined by the detector
        squall_lines = []

        # Extract centroids from convective systems
        centroids = []
        for s in self.systems:
            centroids.append(s.geom.Centroid())

        # Apply DBSCAN clustering method to define squall lines cores using scypy library
        from sklearn.cluster import DBSCAN
        locations = np.array([[c.GetX(), c.GetY()] for c in centroids])
        db = DBSCAN(eps=self.min_distance, min_samples=self.min_nsystems, n_jobs=-1).fit(locations)

        # for each cluster, define a squall line
        unique_labels = set(db.labels_)
        for current_label in unique_labels:
            if current_label == -1:
                continue
            systems_cluster = []
            for i in range(len(db.labels_)):
                if db.labels_[i] == current_label:
                    systems_cluster.append(self.systems[i])

            if len(systems_cluster) >= self.min_nsystems:
                sl = SquallLine(systems_cluster)
                if(sl.linearity_score >= self.linearity_threshold):
                    squall_lines.append(sl)

        return squall_lines
