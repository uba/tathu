#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
from mpl_toolkits.basemap import Basemap

class MapView(object):
    def __init__(self, extent, references=[]):
        # Create a new figure
        self.fig = plt.figure()
        # Create map
        self.bmap = Basemap(llcrnrlon=extent[0], llcrnrlat=extent[1], urcrnrlon=extent[2], urcrnrlat=extent[3], epsg=4326)
        self.references = references
        self.plotReferences()

    def plotReferences(self):
        # Draw references
        self.bmap.drawcoastlines(linewidth=0.4, linestyle='solid', color='white')
        self.bmap.drawcountries(linewidth=0.4, linestyle='solid', color='white')
        self.bmap.drawparallels(np.arange(-90.0, 90.0, 10.0), linewidth=0.25, color='k', labels=[1,0,0,1])
        self.bmap.drawmeridians(np.arange(0.0, 360.0, 10.0), linewidth=0.25, color='k', labels=[1,0,0,1])
        for ref in self.references:
            shp = self.bmap.readshapefile(ref, 'ref', drawbounds=True)
            for nshape, seg in enumerate(self.bmap.ref):
                poly = Polygon(seg, facecolor='none', edgecolor='k')
                plt.gca().add_patch(poly)

    def plotImage(self, image, cmap=None, vmin=None, vmax=None, colorbar=False):
        array = image.ReadAsArray()
        self.plotArray(array, cmap, vmin, vmax, colorbar)

    def plotArray(self, array, cmap=None, vmin=None, vmax=None, colorbar=False):
        self.bmap.imshow(array, origin='upper', cmap=cmap, vmin=vmin, vmax=vmax)
        if(colorbar):
            plt.colorbar(orientation='horizontal')

    def plotPolygons(self, polygons, facecolor='red', alpha=1.0, edgecolor='k', lw=1.0, centroids=False):
        # Centroid coordinates
        x = []
        y = []
        for p in polygons:
            # Extract lat/lon
            lats, lons = self.__extractCoordinates(p)

            # Compute centroid, if requested
            if(centroids):
                centroid = p.Centroid()
                x.append(centroid.GetX())
                y.append(centroid.GetY())

            # Plot polygon
            self.__plotPolygon(lats, lons, facecolor, alpha, lw, edgecolor, self.bmap)

        # Show centroids
        self.bmap.scatter(x, y, marker='.', color='b')

    def __plotPolygon(self, lats, lons, facecolor, alpha, lw, edgecolor, m):
        x, y = m(lons, lats)
        xy = list(zip(x ,y))
        poly = Polygon(xy, facecolor=facecolor, lw=lw, edgecolor=edgecolor, alpha=alpha)
        plt.gca().add_patch(poly)

    def __extractCoordinates(self, polygon):
        lats = []
        lons = []
        points = polygon.GetGeometryRef(0).GetPoints()
        for p in points:
            lons.append(p[0])
            lats.append(p[1])

        return lats, lons

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

        # Create a new figure
        self.fig = plt.figure()

        # Set of axes
        self.axes = []

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
                self.axes.append(plt.subplot2grid((nlines, ncols), (lin, col)))
                i += 1
                if(i == n):
                    break

    def __plotSystems(self):
        # Get geo-extent
        e = self.extent

        # Plot each system
        i = 0
        for s in self.family.systems:
            # Create map
            bmap = Basemap(llcrnrlon=e[0], llcrnrlat=e[1],
                           urcrnrlon=e[2], urcrnrlat=e[3],
                           epsg=4326, ax=self.axes[i])

            bmap.drawmapboundary(fill_color='white')

            self.__plotReferences(bmap)

            if(self.images is not None):
                if(self.images[i] is not None):
                    if(isinstance(self.images[i], np.ndarray)):
                        image = self.images[i]
                    else:
                        image = self.images[i].ReadAsArray()

                    bmap.imshow(image, origin='upper', animated=False)

            # Extract lat/lon
            lats, lons = self.__extractCoordinates(s.geom)

            # Plot polygon
            self.__plotPolygon(lats, lons, 'none', 1.0, 1.0, 'k', bmap, self.axes[i])

            # Extract lat/lon
            lats, lons = self.__extractCoordinates(s.geom.ConvexHull())

            # Plot polygon
            self.__plotPolygon(lats, lons, 'none', 1.0, 1.0, 'red', bmap, self.axes[i])

            if s.timestamp:
                self.axes[i].set_title(s.timestamp.strftime('%H:%M') + ' UTC', fontsize=10, va='center')

            i += 1

        plt.tight_layout(h_pad=2.5)

    def __plotPolygon(self, lats, lons, facecolor, alpha, lw, edgecolor, m, ax):
        x, y = m(lons, lats)
        xy = list(zip(x ,y))
        poly = Polygon(xy, facecolor=facecolor, lw=lw, edgecolor=edgecolor, alpha=alpha)
        plt.sca(ax)
        plt.gca().add_patch(poly)

    def __extractCoordinates(self, polygon):
        lats = []
        lons = []
        points = polygon.GetGeometryRef(0).GetPoints()
        for p in points:
            lons.append(p[0])
            lats.append(p[1])

        return lats, lons

    def __plotReferences(self, bmap):
        #bmap.drawcoastlines(linewidth=0.4, linestyle='solid', color='white')
        bmap.drawcountries(linewidth=0.4, linestyle='solid', color='white')
        bmap.drawparallels(np.arange(-90.0, 90.0, 2.0), linewidth=0.25, color='k', labels=[1,0,0,1])
        bmap.drawmeridians(np.arange(0.0, 360.0, 2.0), linewidth=0.25, color='k', labels=[1,0,0,1])

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

        # Create 3 graphics: polygons, arrays, and timeseries
        axes = []
        axes.append(plt.subplot2grid((2, 2), (0, 0)))
        axes.append(plt.subplot2grid((2, 2), (0, 1)))
        axes.append(plt.subplot2grid((2, 2), (1, 0), colspan=2))

        # Create map
        self.bmap = Basemap(llcrnrlon=self.extent[0], llcrnrlat=self.extent[1],
                            urcrnrlon=self.extent[2], urcrnrlat=self.extent[3], epsg=4326, ax=axes[0])

        self.bmap.drawparallels(np.arange(-90.0, 90.0, 10.0), linewidth=0.25, color='k', labels=[1,0,0,1])
        self.bmap.drawmeridians(np.arange(0.0, 360.0, 10.0), linewidth=0.25, color='k', labels=[1,0,0,1])

        # Create polygon graphic
        self.poly = Polygon([[0, 0], [0,0]], facecolor='none', edgecolor='red', alpha=1.0, lw=1.0)
        axes[0].add_patch(self.poly)

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
        lats, lons = self.__extractCoordinates(self.polygons[i])
        x, y = self.bmap(lons, lats)
        xy = list(zip(x ,y))
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

    def __extractCoordinates(self, polygon):
        lats = []
        lons = []

        points = polygon.GetGeometryRef(0).GetPoints()

        for p in points:
            lons.append(p[0])
            lats.append(p[1])

        return lats, lons

    def __getColorMap(self, n, name='hsv'):
        '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
        RGB color; the keyword argument name must be a standard mpl colormap name.'''
        return plt.cm.get_cmap(name, n)
