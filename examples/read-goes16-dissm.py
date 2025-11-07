#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""

import matplotlib.pyplot as plt

import tathu.constants
from tathu.satellite import goes_r
from tathu.utils import getExtent
from tathu.visualizer import MapView

def viewData(path, extent=None):
    # Get grid from GOES-16 DISSM pre-processed file
    grid = goes_r.rect2grid(path, extent)
    # No remap requested. Get full extent in order to visualize
    if extent is None:
        extent = getExtent(grid.GetGeoTransform(), grid.GetRasterBand(1).ReadAsArray().shape)
    view = MapView(extent)
    view.plotImage(grid, cmap='Greys', colorbar=True, vmin=180.0, vmax=320.0)

path = '.\goes16-dissm\S10635346_202204080000.nc'

# Full-extent + Brazil regions
viewData(path, extent=None)
viewData(path, extent=tathu.constants.REGIAO_NORTE_BRASIL)
viewData(path, extent=tathu.constants.REGIAO_NORDESTE_BRASIL)
viewData(path, extent=tathu.constants.REGIAO_SUDESTE_BRASIL)
viewData(path, extent=tathu.constants.REGIAO_CENTRO_OESTE_BRASIL)
viewData(path, extent=tathu.constants.REGIAO_SUL_BRASIL)

plt.show()
