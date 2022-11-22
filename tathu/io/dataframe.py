#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import geopandas
import pandas as pd

from tathu.geometry.transform import ogr2shapely

def systems2geopandas(systems):
    # Create dataframe with fixed attributes
    df = pd.DataFrame({
        'name': [str(s.name) for s in systems],
        'timestamp': [s.timestamp for s in systems],
        'event': [str(s.event) for s in systems]
    })
    # Add dynamic attributes
    for attr in systems[0].attrs:
        df[attr] = [s.attrs[attr] for s in systems]
        
    # Add geometry
    df['geom'] = [ogr2shapely(s.geom) for s in systems]

    # Add relationships
    df['relationships'] = [s.getRelationshipNamesAsString() for s in systems]

    # Creat geo-dataframe
    gdf = geopandas.GeoDataFrame(df, geometry='geom')

    # Adjust SRS
    gdf = gdf.set_crs('epsg:4326')

    return gdf

class Outputter(object):
    """
    This class can be used to export tracking results to GeoPandas Dataframe.
    """
    def __init__(self):
        self.gdf = None

    def output(self, systems):
        if not systems:
            return
        if self.gdf is None:
            self.gdf = systems2geopandas(systems)
        else:
            self.gdf = self.gdf.append(systems2geopandas(systems))
