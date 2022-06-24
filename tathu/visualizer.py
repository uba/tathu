#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon

class MapView(object):
    def __init__(self, extent, references=[]):
        # Create a new figure
        self.fig = plt.figure()
        # Create map
        self.extent = [extent[0], extent[2], extent[1], extent[3]]
        self.crs = ccrs.PlateCarree()
        self.ax = plt.axes(projection=self.crs)
        self.ax.set_extent(self.extent, crs=self.crs)
        self.references = references
        self.plotReferences()

    def plotReferences(self):
        self.ax.coastlines(linewidth=0.4, linestyle='solid', color='white')
        self.ax.add_feature(cfeature.BORDERS, linewidth=0.4, linestyle='solid', color='white')
        gl = self.ax.gridlines(draw_labels=True, linewidth=0.25, linestyle='--', color='k')
        gl.top_labels = False
        gl.right_labels = False
        for ref in self.references:
            shp = shpreader.Reader(ref).geometries()
            self.ax.add_geometries(shp, self.crs, linewidth=0.4, facecolor='none', edgecolor='k')

    def plotImage(self, image, cmap=None, vmin=None, vmax=None, colorbar=False):
        array = image.ReadAsArray()
        self.plotArray(array, cmap, vmin, vmax, colorbar)

    def plotArray(self, array, cmap=None, vmin=None, vmax=None, colorbar=False):
        im = self.ax.imshow(array, transform=self.crs, cmap=cmap, vmin=vmin, vmax=vmax, extent=self.extent,)
        if colorbar:
            plt.colorbar(im, orientation='vertical', label=self.clabel)

    def plotPolygons(self, polygons, facecolor='red', alpha=1.0, edgecolor='k', lw=1.0, centroids=False):
        # Centroid coordinates
        x, y = [], []
        for p in polygons:
            # Extract lat/lon
            lats, lons = self.__extractCoordinates(p)

            # Compute centroid, if requested
            if(centroids):
                centroid = p.Centroid()
                x.append(centroid.GetX())
                y.append(centroid.GetY())

            # Plot polygon
            self.__plotPolygon(lats, lons, facecolor, alpha, lw, edgecolor)

        # Show centroids
        self.ax.scatter(x, y, marker='.', color='b')

    def __plotPolygon(self, lats, lons, facecolor, alpha, lw, edgecolor):
        xy = list(zip(lons, lats))
        poly = Polygon(xy, facecolor=facecolor, lw=lw, edgecolor=edgecolor, alpha=alpha)
        plt.gca().add_patch(poly)

    def __extractCoordinates(self, polygon):
        lats, lons = [], []
        points = polygon.GetGeometryRef(0).GetPoints()
        for p in points:
            lons.append(p[0])
            lats.append(p[1])
        return lats, lons

    def show(self):
        plt.show()
