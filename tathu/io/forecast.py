#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

from tathu.visualizer import MapView

class Outputter(object):
    """
    This class can be used to show forecast results.
    """
    def __init__(self, systems, forecasts, extent, grid):
        self.systems = systems
        self.forecasts = forecasts
        self.mapview = MapView(extent)
        self.__plotSystems(systems, facecolor='b', edgecolor='b', alpha=0.5)
        self.__plotForecast()
        self.mapview.plotImage(grid, cmap='Greys', vmin=180.0, vmax=320.0)

    def show(self):
        self.mapview.show()

    def __plotSystems(self, systems, facecolor='none', edgecolor='red', alpha=1.0, centroids=False):
        p = [s.geom for s in systems]
        self.mapview.plotPolygons(p, facecolor=facecolor, alpha=alpha, edgecolor=edgecolor, centroids=centroids)

    def __plotForecast(self):
        alpha = 1.0
        for t in self.forecasts:
            self.__plotSystems(self.forecasts[t], edgecolor='red', alpha=alpha, centroids=True)
            alpha *= 0.8
