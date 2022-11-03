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
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon

from tathu.geometry.utils import extractCoordinates

class MapView(object):
    def __init__(self, extent, references=[], clabel='', timestamp=None):
        # Create a new figure
        self.fig = plt.figure()
        # Get parameters
        self.clabel = clabel
        self.timestamp = timestamp
        # Create map
        self.extent = [extent[0], extent[2], extent[1], extent[3]]
        self.crs = ccrs.PlateCarree()
        self.ax = plt.axes(projection=self.crs)
        self.ax.set_extent(self.extent, crs=self.crs)
        # Setup title, if necessary
        if self.timestamp:
            self.ax.set_title('Systems ' + self.timestamp)
        self.references = references
        self.plotReferences()

    def plotReferences(self):
        self.ax.coastlines(linewidth=0.4, linestyle='solid', color='lightgray')
        self.ax.add_feature(cfeature.BORDERS, linewidth=0.4, linestyle='solid', color='lightgray')
        gl = self.ax.gridlines(draw_labels=True, linewidth=0.25, linestyle='--', color='gray')
        gl.top_labels = False
        gl.right_labels = False
        for ref in self.references:
            shp = shpreader.Reader(ref).geometries()
            self.ax.add_geometries(shp, self.crs, linewidth=0.4, facecolor='none', edgecolor='lightgray')

    def plotImage(self, image, cmap=None, vmin=None, vmax=None, colorbar=False):
        nodata = image.GetRasterBand(1).GetNoDataValue()
        array = np.ma.masked_equal(image.ReadAsArray(), nodata)
        self.plotArray(array, cmap, vmin, vmax, colorbar)

    def plotArray(self, array, cmap=None, vmin=None, vmax=None, colorbar=False):
        im = self.ax.imshow(array, transform=self.crs, cmap=cmap, vmin=vmin, vmax=vmax, extent=self.extent)
        if colorbar:
            plt.colorbar(im, orientation='vertical', label=self.clabel)

    def plotSystems(self, systems, facecolor='red', alpha=1.0, edgecolor='k', lw=1.0, centroids=False):
        polygons = [s.geom for s in systems]
        self.plotPolygons(polygons, facecolor, alpha, edgecolor, lw, centroids)

    def plotPolygons(self, polygons, facecolor='red', alpha=1.0, edgecolor='k', lw=1.0, centroids=False):
        # Centroid coordinates
        x, y = [], []
        for p in polygons:
            # Extract lat/lon
            lats, lons = extractCoordinates(p)

            # Compute centroid, if requested
            if centroids:
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
    def __init__(self, family, images=None, extent=None, highlightEvent=True):
        # Systems that will be plotted
        self.family = family

        # Images information (optional)
        self.images = images

        # Image extent
        if extent is None:
            self.extent = family.getExtent()
        else:
            self.extent = extent

        # Colors for system event
        self.colors = {
            'SPONTANEOUS_GENERATION': 'green',
            'MERGE': 'blue',
            'SPLIT': 'yellow',
            'CONTINUITY': 'red'
        }

        # Flag that indicates if plot will highlight system events
        self.highlightEvent = highlightEvent

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

        # Add legend
        patchList = []
        for key in self.colors:
            data_key = mpatches.Patch(color=self.colors[key], label=key)
            patchList.append(data_key)

        self.fig.legend(handles=patchList, loc='lower right',
            ncol=4, bbox_transform=self.fig.transFigure, borderaxespad=0)

    def show(self):
        plt.show()

    def __createPlotGrid(self):
        # Compute number of cols and lines
        ncols = 6
        n = len(self.family.systems)
        nlines = int(n / ncols + 1)
        # Define size of figure according to ncols/nlines
        plt.gcf().set_size_inches(ncols*2, nlines*2, forward=True)

        # Create individual plots
        i = 0
        self.axes = []
        for lin in range(nlines):
            if i == n:
                break
            for col in range(ncols):
                ax = plt.subplot2grid((nlines, ncols), (lin, col), projection=self.crs)
                ax.set_extent(self.extent, crs=self.crs)
                self.axes.append(ax)
                i += 1
                if i == n:
                    break

    def __plotSystems(self):
        # Get geo-extent
        e = self.extent

        # Plot each system
        i = 0
        for s in self.family.systems:
            self.__plotReferences(self.axes[i])

            if self.images is not None:
                if self.images[i] is not None:
                    if isinstance(self.images[i], np.ndarray):
                        image = self.images[i]
                    else:
                        image = self.images[i].ReadAsArray()

                    self.axes[i].imshow(image, transform=self.crs, extent=self.extent)

            # Extract lat/lon
            lats, lons = extractCoordinates(s.geom)

            # Plot polygon
            self.__plotPolygon(lats, lons, 'none', 1.0, 1.0, 'k', self.axes[i])

            # Extract lat/lon
            lats, lons = extractCoordinates(s.geom.ConvexHull())

            # Plot polygon
            color = 'red'
            if self.highlightEvent:
                color = self.colors[s.event]
            self.__plotPolygon(lats, lons, 'none', 1.0, 1.0, color, self.axes[i])

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


class AnimationMap(animation.TimedAnimation):
    def __init__(self, family, attributes):
        self.extent = family.getExtent()
        self.polygons = family.getPolygons()
        self.arrays = family.getRasters()
        self.timestamps = family.getTimestamps()
        self.timeseries = []
        for name in attributes:
            self.timeseries.append(family.getAttribute(name))

        fig = plt.figure()

        # Adjust for cartopy format
        self.extent = [self.extent[0], self.extent[2],
            self.extent[1], self.extent[3]]

        # SRS
        self.crs = ccrs.PlateCarree()

        # Create 3 graphics: polygons, arrays, and timeseries
        axes = []
        axes.append(plt.subplot2grid((2, 2), (0, 0), projection=self.crs))
        axes.append(plt.subplot2grid((2, 2), (0, 1)))
        axes.append(plt.subplot2grid((2, 2), (1, 0), colspan=2))

        # Adjust map extent
        self.map = axes[0]
        self.map.set_extent(self.extent, crs=self.crs)

        # Draw grids
        gl = self.map.gridlines(draw_labels=True, linewidth=0.25, linestyle='--', color='k')
        gl.top_labels = False
        gl.right_labels = False

        # Create polygon graphic
        self.poly = Polygon([[0, 0], [0,0]], facecolor='none', edgecolor='red', alpha=1.0, lw=1.0)
        self.map.add_patch(self.poly)

        # Create axis for timeseries (multi-scale using twinx)
        self.tsAxes = [axes[2]]
        for i in range(1, len(attributes)):
            self.tsAxes.append(axes[2].twinx())
            self.tsAxes[i].set_xticklabels([])

        # Get color for each timeseries
        cmap = self.__getColorMap(len(attributes), 'Dark2')

        # Create line for each timeseries
        self.x = []
        self.lines = []

        for i in range(0, len(attributes)):
            self.x.append(np.arange(len(self.timeseries[i])))
            line = Line2D([], [], color=cmap(i), marker='o', label=attributes[i])
            self.lines.append(line)
            self.tsAxes[i].add_line(line)
            self.tsAxes[i].set_xlim(0, len(self.timeseries[i]))
            self.tsAxes[i].set_ylim(min(self.timeseries[i]), max(self.timeseries[i]))

        # Add legend
        labs = [l.get_label() for l in self.lines]
        self.tsAxes[0].legend(self.lines, labs, loc='upper right')

        # Extract hour minute
        hourmin = [t.strftime('%H:%M') for t in self.timestamps]

        # Show timestamp information
        axes[2].set_xticks(self.x[0])
        axes[2].set_xticklabels(hourmin, rotation=45)

        self.array = axes[1].imshow(self.arrays[0])
        axes[1].get_xaxis().set_visible(False)
        axes[1].get_yaxis().set_visible(False)
        axes[1].set_facecolor((0, 0, 0))

        animation.TimedAnimation.__init__(self, fig, interval=200, blit=False, repeat_delay=2000)

    def show(self):
        plt.show()

    def _draw_frame(self, framedata):
        # Frame number
        i = framedata

        # Animate array
        self.array.set_array(self.arrays[i])
        self.array.set_extent((0, self.arrays[i].shape[1], 0, self.arrays[i].shape[0]))

        # Animate polygon
        lats, lons = extractCoordinates(self.polygons[i])
        xy = list(zip(lons, lats))
        self.poly.set_xy(xy)

        toDraw = []
        toDraw.append(self.poly)

        # Animate lines
        for k in range(0, len(self.lines)):
            self.lines[k].set_data(self.x[k][0:i+1], self.timeseries[k][0:i+1])
            toDraw.append(self.lines[k])

        self._drawn_artists = toDraw

    def new_frame_seq(self):
        return iter(list(range(len(self.polygons))))

    def _init_draw(self):
        pass

    def __getColorMap(self, n, name='hsv'):
        '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
        RGB color; the keyword argument name must be a standard mpl colormap name.'''
        return plt.cm.get_cmap(name, n)

class AnimationMapDatabase(animation.TimedAnimation):
    def __init__(self, db, extent, images, timestamps, cmap='Greys'):
        self.db = db
        self.extent = extent
        self.images = images
        self.timestamps = timestamps
        self.cmap = cmap

        fig = plt.figure()

        # Adjust for cartopy format
        self.extent = [self.extent[0], self.extent[2],
            self.extent[1], self.extent[3]]

        # SRS
        self.crs = ccrs.PlateCarree()

        # Create map
        self.map = plt.axes(projection=self.crs)
        self.map.set_extent(self.extent, crs=self.crs)

        # Draw grids
        gl = self.map.gridlines(draw_labels=True, linewidth=0.25, linestyle='--', color='k')
        gl.top_labels = False
        gl.right_labels = False

        self.array = self.map.imshow(self.__getArray(self.images[0]),
            transform=self.crs, cmap=self.cmap, extent=self.extent)

        self.colors = {
            'SPONTANEOUS_GENERATION': 'green',
            'MERGE': 'blue',
            'SPLIT': 'yellow',
            'CONTINUITY': 'red'
        }

        # Add legend
        patchList = []
        for key in self.colors:
            data_key = mpatches.Patch(color=self.colors[key], label=key)
            patchList.append(data_key)

        plt.legend(handles=patchList, loc='upper right')

        # Add title
        self.map.set_title(self.timestamps[0].strftime("%Y-%m-%d %H:%M:%S UTC"))

        # Plot references
        self.map.coastlines(linewidth=0.4, linestyle='solid', color='black')
        self.map.add_feature(cfeature.BORDERS, linewidth=0.4, linestyle='solid', color='black')

        animation.TimedAnimation.__init__(self, fig, interval=500, blit=False, repeat_delay=2000)

    def show(self):
        plt.show()

    def _draw_frame(self, framedata):
        # Frame number
        i = framedata

        # Remove old geometries
        [p.remove() for p in reversed(self.map.patches)]

        # Update image
        self.array.set_array(self.__getArray(self.images[i]))

        # Update title
        self.map.set_title(self.timestamps[i].strftime("%Y-%m-%d %H:%M:%S UTC"))

        # Load systems
        systems = self.db.loadByDate('%Y%m%d%H%M', self.timestamps[i].strftime('%Y%m%d%H%M'), attrs=['nae'])

        # Create polygon graphic
        for s in systems:
            lats, lons = extractCoordinates(s.geom)
            xy = list(zip(lons, lats))
            poly = Polygon(xy, facecolor='none', edgecolor=self.colors[s.event],
                alpha=1.0, lw=1.0, label=s.event)
            self.map.add_patch(poly)

    def new_frame_seq(self):
        return iter(list(range(len(self.timestamps))))

    def _init_draw(self):
        pass

    def __getArray(self, image):
        if isinstance(image, np.ndarray):
            return image
        return image.ReadAsArray()

