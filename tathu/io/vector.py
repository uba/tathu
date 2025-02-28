#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import json
from osgeo import ogr, osr

class Outputter(object):
    """
    This class can be used to export tracking results to a vector geo-file (e.g. ESRI Shapefile, KML, etc.)
    """
    def __init__(self, path, format, options=[]):
        self.path = path
        self.format = format

        # Create output file
        self.driver = ogr.GetDriverByName(format)
        self.datasource = self.driver.CreateDataSource(path)

        # SRS
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)

        # Create spatial layer
        self.layer = self.datasource.CreateLayer('', srs, ogr.wkbPolygon, options)

        self.__createFixedAttributes()

    def output(self, systems):
        # Systems is empty?
        if not systems:
            return

        ## Add numeric attributes to field names ##
        # Get first system to extract numeric attributes names
        attrs = systems[0].attrs
        self.__createNumericAttributes(attrs)

        # For each system
        for s in systems:
            self.layer.CreateFeature(self.__buildSystemFeature(s))

    def __createFixedAttributes(self):
        self.layer.CreateField(ogr.FieldDefn('name', ogr.OFTString))
        self.layer.CreateField(ogr.FieldDefn('timestamp', ogr.OFTString))
        self.layer.CreateField(ogr.FieldDefn('event', ogr.OFTString))

    def __createNumericAttributes(self, attrs):
        for a in attrs:
            self.layer.CreateField(ogr.FieldDefn(a, ogr.OFTReal))

    def __buildSystemFeature(self, system):
        defn = self.layer.GetLayerDefn()
        feature = ogr.Feature(defn)
        # Fill fixed attributes
        feature.SetField('name', str(system.name))
        feature.SetField('timestamp', str(system.timestamp))
        feature.SetField('event', str(system.event))
        # Fill numeric attributes
        for name in system.attrs:
            feature.SetField(name, system.attrs[name])
        # Setup geometry
        feature.SetGeometry(system.geom)

        return feature

class Shapefile(Outputter):
    """
    Auxiliary class that can be used to export tracking results to ESRI Shapefile.
    """
    def __init__(self, path, options=[]):
        super(Shapefile, self).__init__(path, 'ESRI Shapefile', options)

class KML(Outputter):
    """
    Auxiliary class that can be used to export tracking results to Google Keyhole Markup Language file (KML).
    """
    def __init__(self, path, options=[]):
        super(KML, self).__init__(path, 'KML', options)

class GeoJSON(Outputter):
    """
    Auxiliary class that can be used to export tracking results to GeoJSON files.
    """
    def __init__(self, path, options=[], compact=True):
        self.compact = compact
        super(GeoJSON, self).__init__(path, 'GeoJSON', options)

    def output(self, systems):
        try:
            super().output(systems)
        except:
            pass
        else:
            self.datasource = None
            if self.compact:
                with open(self.path, 'r') as f:
                    data = json.load(f)
                with open(self.path, 'w') as f:
                    json.dump(data, f, separators=(',', ':'))


