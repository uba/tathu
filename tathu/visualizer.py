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

from tathu.geometry.utils import extractCoordinates

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
        im = self.ax.imshow(array, transform=self.crs, cmap=cmap, vmin=vmin, vmax=vmax, extent=self.extent)
        if colorbar:
            plt.colorbar(im, orientation='vertical', label=self.clabel)

    def plotPolygons(self, polygons, facecolor='red', alpha=1.0, edgecolor='k', lw=1.0, centroids=False):
        # Centroid coordinates
        x, y = [], []
        for p in polygons:
            # Extract lat/lon
            lats, lons = extractCoordinates(p)

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

    def show(self):
        plt.show()

class SystemHistoryView:
    def __init__(self, family, images=None, extent=None):
        # Systems that will be plotted
        self.family = family

        # Images information (optional)
        self.images = images

        # Image extent
        if(extent is None):
            self.extent = family.getExtent()
        else:
            self.extent = extent
        
        # Adjust for cartopy format
        self.extent = [self.extent[0], self.extent[2],
            self.extent[1], self.extent[3]]

        # Create a new figure
        self.fig = plt.figure()

        # Set of axes
        self.axes = []

        # SRS
        self.crs = ccrs.PlateCarree()

        # Build plot grid
        self.__createPlotGrid()

        # Draw!
        self.__plotSystems()

    def show(self):
        plt.show()

    def __createPlotGrid(self):
        # Compute number of cols and lines
        ncols = 6
        n = len(self.family.systems)
        nlines = int(n / ncols + 1)

        # Create individual plots
        i = 0
        self.axes = []
        for lin in range(nlines):
            for col in range(ncols):
                ax = plt.subplot2grid((nlines, ncols), (lin, col), projection=self.crs)
                ax.set_extent(self.extent, crs=self.crs)
                self.axes.append(ax)
                i += 1
                if(i == n):
                    break

    def __plotSystems(self):
        # Get geo-extent
        e = self.extent

        # Plot each system
        i = 0
        for s in self.family.systems:
            self.__plotReferences(self.axes[i])

            if(self.images is not None):
                if(self.images[i] is not None):
                    if(isinstance(self.images[i], np.ndarray)):
                        image = self.images[i]
                    else:
                        image = self.images[i].ReadAsArray()

                    self.ax.imshow(image, transform=self.crs, extent=self.extent)

            # Extract lat/lon
            lats, lons = extractCoordinates(s.geom)

            # Plot polygon
            self.__plotPolygon(lats, lons, 'none', 1.0, 1.0, 'k', self.axes[i])

            # Extract lat/lon
            lats, lons = extractCoordinates(s.geom.ConvexHull())

            # Plot polygon
            self.__plotPolygon(lats, lons, 'none', 1.0, 1.0, 'red', self.axes[i])

            if s.timestamp:
                self.axes[i].set_title(s.timestamp.strftime('%H:%M') + ' UTC', fontsize=10, va='center')

            i += 1

        plt.tight_layout(h_pad=2.5)

    def __plotPolygon(self, lats, lons, facecolor, alpha, lw, edgecolor, ax):
        xy = list(zip(lons, lats))
        poly = Polygon(xy, facecolor=facecolor, lw=lw, edgecolor=edgecolor, alpha=alpha)
        plt.sca(ax)
        plt.gca().add_patch(poly)

    def __plotReferences(self, ax):
        ax.coastlines(linewidth=0.4, linestyle='solid', color='white')
        ax.add_feature(cfeature.BORDERS, linewidth=0.4, linestyle='solid', color='white')
        gl = ax.gridlines(draw_labels=True, linewidth=0.25, linestyle='--', color='k')
        gl.top_labels = False
        gl.right_labels = False
