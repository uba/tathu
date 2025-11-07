#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

from osgeo import osr

# Define KM_PER_DEGREE
KM_PER_DEGREE = 40075.16/360.0

# Define METERS_PER_DEGREE
METERS_PER_DEGREE = KM_PER_DEGREE * 1000.0

# Define Lat/Lon WSG84 Spatial Reference System (EPSG:4326)
LAT_LON_WGS84 = osr.SpatialReference()
LAT_LON_WGS84.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')

# Some regions extents
LAT_LONG_WGS84_SOUTH_AMERICA_EXTENT = [-88.02, -46.50, -26.22, 12.54]
LAT_LONG_WGS84_BRAZIL_NORTH_EXTENT = [-74.50, -14.00, -45.50, 5.40]
LAT_LONG_WGS84_BRAZIL_NORTHEAST_EXTENT = [-49.00, -18.20, -34.30, 0.0]
LAT_LONG_WGS84_BRAZIL_SOUTHEAST_EXTENT = [-53.20, -25.50, -39.00, -13.50]
LAT_LONG_WGS84_BRAZIL_MIDWEST_EXTENT = [-61.50, -24.10, -45.35, -6.40]
LAT_LONG_WGS84_BRAZIL_SOUTH_EXTENT = [-58.10, -34.15, -47.20, -22.00]

# pt-BR version of extents (syntax sugar purposes)
REGIAO_AMERICA_DO_SUL = LAT_LONG_WGS84_SOUTH_AMERICA_EXTENT
REGIAO_NORTE_BRASIL = LAT_LONG_WGS84_BRAZIL_NORTH_EXTENT
REGIAO_NORDESTE_BRASIL = LAT_LONG_WGS84_BRAZIL_NORTHEAST_EXTENT
REGIAO_SUDESTE_BRASIL = LAT_LONG_WGS84_BRAZIL_SOUTHEAST_EXTENT
REGIAO_CENTRO_OESTE_BRASIL = LAT_LONG_WGS84_BRAZIL_MIDWEST_EXTENT
REGIAO_SUL_BRASIL = LAT_LONG_WGS84_BRAZIL_SOUTH_EXTENT

# Hour values (i.e. ['00', '01, ..., '12', .., '20, '23'])
HOURS = [str(i).zfill(2) for i in range(0, 24)]
