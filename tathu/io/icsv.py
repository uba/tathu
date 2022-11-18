#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import csv
import os

class Outputter(object):
    """
    This class can be used to export tracking results to CSV files.
    """
    def __init__(self, path, writeHeader=True, delimiter=',', outputGeom=False,
            outputCentroid=False, outputRelationships=True, precision=4):
        self.path = path
        self.writeHeader = writeHeader
        self.delimiter = delimiter
        self.outputGeom = outputGeom
        self.outputCentroid = outputCentroid
        self.outputRelationships = outputRelationships
        self.precision = precision

    def output(self, systems):
        # Systems is empty?
        if not systems:
            return

        if isinstance(systems, list):
            systems = self.__systemlist2dic(systems)

        # Build field names (start with fixed attributes)
        fieldnames = ['name', 'timestamp', 'event']

        if self.outputGeom:
            fieldnames.append('geom')

        if self.outputCentroid:
            fieldnames.append('centroid')

        if self.outputRelationships:
            fieldnames.append('relationships')

        ## Add numeric attributes to field names ##

        # Get first system to extract numeric attributes names
        attrs = list(systems.values())[0][0].attrs
        for key in attrs:
            fieldnames.append(key)

        needHeaderWriting = False
        if not os.path.exists(self.path):
            needHeaderWriting = True

        # Create .csv file and write each system
        with open(self.path, 'at+', newline='') as file:
            writer = csv.DictWriter(file, delimiter=self.delimiter, fieldnames=fieldnames)
            # Write header if necessary
            if self.writeHeader and needHeaderWriting:
                writer.writeheader()

            # For each system family
            for family in systems:
                # For each system member of current family:
                for s in systems[family]:
                    # Write!
                    writer.writerow(self.__system2dic(s))

    def __system2dic(self, system):
            # Start with fixed attributes
            sdic = {'name' : system.name, 'timestamp' : system.timestamp, 'event' : str(system.event)}

            # Include geometry attribute, if requested
            if self.outputGeom:
                sdic['geom'] = system.geom.ExportToWkt()

            # Include geometry centroid, if requested
            if self.outputCentroid:
                sdic['centroid'] = system.geom.Centroid().ExportToWkt()

            # Include system relations, if requested
            if self.outputRelationships:
                sdic['relationships'] = system.getRelationshipNamesAsString()

            # Add numeric attributes and ajust float precision
            sdic.update(system.attrs)
            for attr in system.attrs:
                if isinstance(sdic[attr], float):
                    sdic[attr] = round(sdic[attr], self.precision)

            return sdic

    def __systemlist2dic(self, systems):
        dic = {}
        i = 0
        for s in systems:
            dic[i] = [s]
            i += 1
        return dic

