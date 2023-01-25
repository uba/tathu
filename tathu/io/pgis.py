#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import io
import uuid
from datetime import datetime

import numpy as np
import psycopg2
import psycopg2.extras
from osgeo import ogr

from tathu.tracking.system import ConvectiveSystem, ConvectiveSystemFamily

def bytea2nparray(bytea):
    '''Converts Numpy Array from Postgres to python.'''
    bdata = io.BytesIO(bytea)
    bdata.seek(0)
    return np.load(bdata)

def _adapt_array(text):
    '''Converts Numpy Array from python to Postgres.'''
    out = io.BytesIO()
    np.save(out, text)
    out.seek(0)
    return psycopg2.Binary(out.read())

psycopg2.extensions.register_adapter(np.ndarray, _adapt_array)

class Outputter(object):
    """
    This class can be used to export tracking results to Postgres/PostGIS Database.
    """
    def __init__(self, host, database, user, pwd, table, attrs, outputRaster=True, raster2int=True):
        # Store parameters
        self.host = host
        self.database = database
        self.user = user
        self.password = pwd
        self.table = table
        self.attrs = attrs
        self.outputRaster = outputRaster
        self.raster2int = raster2int # Convert raster to int16 (disk-usage)?

        # Prepare connection
        self.conn = psycopg2.connect(host=host, database=database, user=user, password=pwd)

        # Create table
        self.__createTable(table)

    def __del__(self):
        self.conn.close()

    def output(self, systems):
        # Systems is empty?
        if not systems:
            return

        cur = self.conn.cursor()

        for s in systems:
            self.__insertSystem(s, cur)

        cur.close()

        self.conn.commit()

    def __createTable(self, table):

        try:
            # Build numeric attributes creation command
            # For while, using REAL for all
            # TODO: create a map that relates attrs <-> data type on ConvectiveSystem class
            # Can use Numpy types, like np.int16, np.float, etc.?
            dynamicAttributes = ''
            for attr in self.attrs:
                dynamicAttributes += attr + ' REAL, '

            cmd = '''CREATE TABLE IF NOT EXISTS ''' + table + '''(
                id SERIAL PRIMARY KEY,
                name uuid,
                date_time timestamp(0) without time zone, ''' + dynamicAttributes + '''
                event VARCHAR(64),
                relations varchar(36)[],
                raster bytea,
                nodata INTEGER,
                geotransform real[6],
                geom GEOMETRY(POLYGON, 4326))'''

            cur = self.conn.cursor()
            cur.execute(cmd)
            cur.close()
            self.conn.commit()

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

    def __system2tuple(self, s):
        # Prepare raster data
        if self.outputRaster:
            nodata = s.nodata
            raster = s.raster.filled(fill_value=nodata)
            # Convert if requested
            if self.raster2int:
                raster = np.ma.masked_where(raster == nodata, raster)
                nodata = np.iinfo(np.int16).min
                raster = raster * 100
                raster = raster.filled(fill_value=nodata)
                raster = raster.astype(np.int16)
        else:
            nodata, raster = 0, np.zeros((1,1))

        # Build system-tuple
        tuple = (str(s.name), s.timestamp)
        for name in self.attrs:
            tuple += (s.attrs[name],)

        tuple += (str(s.event), s.getRelationshipNames(), raster, nodata, list(s.geotransform), s.getGeomWKT())

        return tuple

    def __insertSystem(self, s, cur):
        cmd = '''INSERT INTO ''' + self.table + ''' VALUES (default, %s, %s, '''
        for attr in self.attrs:
            cmd += '%s, '
        cmd += '''%s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326))'''
        cur.execute(cmd, self.__system2tuple(s))

class Loader(object):
    """
    This class can be used to load tracking results from Postgres/PostGIS Database.
    """
    def __init__(self, host, database, user, pwd, table):
        # Store parameters
        self.host = host
        self.database = database
        self.user = user
        self.password = pwd
        self.table = table

        # Prepare connection
        self.conn = psycopg2.connect(host=host, database=database, user=user, password=pwd)

    def loadNames(self):
        try:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute('SELECT DISTINCT name FROM ' + self.table)

            names = [row['name'] for row in cur.fetchall()]

            cur.close()

            return names

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

    def loadDates(self):
        try:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute('SELECT DISTINCT date_time FROM ' + self.table + ' ORDER BY(date_time)')

            t = [row['date_time'] for row in cur.fetchall()]

            cur.close()

            return t

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

    def loadSystemsByDate(self, date):
        try:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute('SELECT name FROM ' + self.table + ' WHERE date_time = \'' + str(date) + '\'')

            systems = []

            for row in cur.fetchall():
                systems.append(self.loadSystem(row['name'], [], date))

            cur.close()

            return systems

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

    def load(self, name, attrs):
        try:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            query = 'SELECT *, ST_AsBinary(geom) as wkb FROM ' + self.table + ' WHERE name=\'' + name + '\' ORDER BY (date_time)'''

            cur.execute(query)

            # Create family
            family = ConvectiveSystemFamily()

            for row in cur.fetchall():
                # Load geometry and create object
                s = ConvectiveSystem(ogr.CreateGeometryFromWkb(bytes(row['wkb'])))

                # Load numeric attributes
                s.name = uuid.UUID(row['name'])
                s.timestamp = datetime.strptime(str(row['date_time']), '%Y-%m-%d %H:%M:%S')

                for name in attrs:
                    s.attrs[name] = row[name]

                s.event = row['event']

                # Load raster data
                raster = bytea2nparray(row['raster'])
                nodata = row['nodata']

                # Apply mask
                raster = np.ma.masked_where(raster == nodata, raster, False)

                s.raster = raster/100
                s.nodata = nodata/100
                s.geotransform = row['geotransform']

                s.relationships = row['relations']

                family.addSystem(s)

            cur.close()

            return family

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

    def loadSystem(self, name, attrs, date=None):
        try:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            query = 'SELECT *, ST_AsBinary(geom) as wkb FROM ' + self.table + ' WHERE name=\'' + name + '\''
            query += ' AND date_time = \'' + str(date) + '\''
            query += ' ORDER BY (date_time)'

            cur.execute(query)

            for row in cur.fetchall():
                # Load geometry and create object
                s = ConvectiveSystem(ogr.CreateGeometryFromWkb(bytes(row['wkb'])))

                # Load numeric attributes
                s.name = uuid.UUID(row['name'])
                s.timestamp = datetime.strptime(str(row['date_time']), '%Y-%m-%d %H:%M:%S')

                for name in attrs:
                    s.attrs[name] = row[name]

                s.event = row['event']

                # Load raster data
                raster = bytea2nparray(row['raster'])
                nodata = row['nodata']

                # Apply mask
                raster = np.ma.masked_where(raster == nodata, raster, False)

                s.raster = raster/100
                s.nodata = nodata/100
                s.geotransform = row['geotransform']

                s.relationships = row['relations']

                cur.close()

                return s

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

    def query(self, query):
        try:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            cur.execute(query)

            results = cur.fetchall()

            cur.close()

            return results
            
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)