#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import bz2
import io
import os
import pickle
import sqlite3
import uuid
import zlib
from datetime import datetime

import numpy as np
from osgeo import ogr

from tathu.tracking.system import ConvectiveSystem, ConvectiveSystemFamily

compressor = 'zlib'  # none, zlib, bz2

def adapt_array(arr):
    """
    http://stackoverflow.com/a/31312102/190597 (SoulNibbler)
    """
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    if compressor == 'none':
        return sqlite3.Binary(out.read())
    elif compressor == 'zlib':
        return sqlite3.Binary(zlib.compress(out.read()))
    else:
        return sqlite3.Binary(out.read().encode(compressor))

def convert_array(text):
    out = io.BytesIO(text)
    out.seek(0)
    if compressor == 'zlib':
        out = io.BytesIO(zlib.decompress(out.read()))
    elif compressor == 'bz2':
        out = io.BytesIO(bz2.decompress(out.read()))
    return np.load(out)

# Register Numpy Array adapter and converter
sqlite3.register_adapter(np.ndarray, adapt_array)
sqlite3.register_converter('array', convert_array)

def adapt_tuple(tuple):
    return pickle.dumps(tuple)

def adapt_list(list):
    return pickle.dumps(list)

# Register Python tuples adapter and converter
sqlite3.register_adapter(tuple, adapt_tuple)
sqlite3.register_converter('tuple', pickle.loads)

# Register Python tuples adapter and converter
sqlite3.register_adapter(list, adapt_list)
sqlite3.register_converter('list', pickle.loads)

class Outputter(object):
    """
    This class can be used to export tracking results to SQLite/SpatiaLite Database.
    """
    def __init__(self, database, table, attrs, outputRaster=True, raster2int=True):
        # Store parameters
        self.database = database
        self.table = table
        self.attrs = attrs
        self.outputRaster = outputRaster
        self.raster2int = raster2int # Convert raster to int16 (disk-usage)?

        try:
            # Verify if is necessary call InitSpatialMetadata() function
            initSpatialMetadata = False
            if not os.path.exists(database):
                initSpatialMetadata = True

            # Make connection
            self.conn = sqlite3.connect(database, detect_types=sqlite3.PARSE_DECLTYPES)
            self.conn.row_factory = sqlite3.Row

            # Load spatial extension (SpatiaLite)
            self.conn.enable_load_extension(True)
            self.conn.execute('SELECT load_extension("mod_spatialite")')

            # Create spatial metadata tables, if necessary
            if initSpatialMetadata:
                cur = self.conn.cursor()
                cur.execute("SELECT InitSpatialMetadata(1)")
                cur.close()

            # Create table
            self.__createTable(table)

        except sqlite3.Error as e:
            print(e)

    def __del__(self):
        self.conn.close()

    def output(self, systems):
        try:
            # Systems is empty?
            if not systems:
                return

            cur = self.conn.cursor()

            for s in systems:
                self.__insertSystem(s, cur)

            cur.close()

            self.conn.commit()

        except sqlite3.Error as e:
            print(e)

    def __tableExists(self, table):
        cur = self.conn.cursor()
        cmd = "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='" + table + "'"
        cur.execute(cmd)
        exists = False
        if cur.fetchone()[0] == 1:
            exists = True
        cur.close()
        return exists

    def __createTable(self, table):
        if self.__tableExists(table):
            return

        try:
            # Build numeric attributes creation command
            # For while, using REAL for all
            # TODO: create a map that relates attrs <-> data type on ConvectiveSystem class
            # Can use Numpy types, like np.int16, np.float, etc.?
            dynAttributes = ''
            for attr in self.attrs:
                dynAttributes += attr + ' REAL, '

            cmd = '''CREATE TABLE IF NOT EXISTS ''' + table + '''(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                date_time TIMESTAMP, ''' + dynAttributes + '''
                event VARCHAR(64),
                relationships TEXT,
                raster array,
                nodata INTEGER,
                geotransform tuple)'''

            cur = self.conn.cursor()
            r = cur.execute(cmd)

            # Add geometry field
            cmd = "SELECT AddGeometryColumn('" + table + "'" + ''', 'geom', 4326, 'POLYGON', 'XY')'''
            cur.execute(cmd)

            cur.close()
        except sqlite3.Error as e:
            print(e)

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
        tuple = (None, str(s.name), s.timestamp)
        for name in self.attrs:
            tuple += (s.attrs[name],)

        tuple += (str(s.event), s.getRelationshipNamesAsString(), raster, nodata, s.geotransform, s.getGeomWKT())

        return tuple

    def __insertSystem(self, s, cur):
        cmd = '''INSERT INTO ''' + self.table + ''' VALUES (?, ?, ?, '''
        for attr in self.attrs:
            cmd += '?, '
        cmd += '''?, ?, ?, ?, ?, ST_GeomFromText(?, 4326))'''
        cur.execute(cmd, self.__system2tuple(s))

class Loader(object):
    """
    This class can be used to load tracking results from SQLite/SpatiaLite Database.
    """
    def __init__(self, database, table):
        # Store parameters
        self.database = database
        self.table = table

        try:
            # Make connection
            self.conn = sqlite3.connect(database, detect_types=sqlite3.PARSE_DECLTYPES)
            self.conn.row_factory = sqlite3.Row

            # Load spatial extension (SpatiaLite)
            self.conn.enable_load_extension(True)
            self.conn.execute('SELECT load_extension("mod_spatialite")')

        except sqlite3.Error as e:
            print(e)

    def __del__(self):
        self.conn.close()

    def loadNames(self):
        try:
            cur = self.conn.cursor()
            cur.execute('SELECT DISTINCT name FROM ' + self.table)

            names = [row['name'] for row in cur.fetchall()]

            cur.close()

            return names

        except sqlite3.Error as e:
            print(e)

    def loadByDuration(self, hours, operator='>='):
        try:
            sql = '''SELECT DISTINCT name FROM
                    (SELECT name, cast((strftime('%s', max(date_time)) - strftime('%s', min(date_time))) as real)/60/60 AS elapsed_time
                    FROM ''' + self.table + ''' GROUP BY name) AS duration WHERE elapsed_time ''' + operator + str(hours) + ''' ORDER BY elapsed_time DESC'''

            cur = self.conn.cursor()
            cur.execute(sql)

            names = [row['name'] for row in cur.fetchall()]

            cur.close()

            return names

        except sqlite3.Error as e:
            print(e)

    def loadByInterval(self, start, end):
        try:
            sql = '''SELECT DISTINCT name FROM
                    (SELECT name, cast((strftime('%s', max(date_time)) - strftime('%s', min(date_time))) as real)/60/60 AS elapsed_time
                    FROM ''' + self.table + ''' GROUP BY name) AS duration WHERE elapsed_time >=''' + str(start) + '''
                    AND elapsed_time <=''' + str(end) + ''' ORDER BY elapsed_time DESC'''

            cur = self.conn.cursor()
            cur.execute(sql)

            names = [row['name'] for row in cur.fetchall()]

            cur.close()

            return names

        except sqlite3.Error as e:
            print(e)

    def getLastDate(self, format='%Y%m%d'):
        try:
            cur = self.conn.cursor()
            cur.execute('SELECT strftime(\'' + format + '\', MAX(date_time)) FROM ' + self.table)

            date = None
            for row in cur.fetchall():
                date = row[0]

            cur.close()

            return datetime.strptime(date, format)

        except sqlite3.Error as e:
            print(e)

    def loadLastSystems(self, attrs):
        try:
            date = self.getLastDate('%Y-%m-%d %H:%M:00')
            cur = self.conn.cursor()
            cur.execute('SELECT *, ST_AsBinary(geom) as wkb FROM ' + self.table + ' WHERE date_time=\'' + date + '\'')
            return self.__fetchSystems(cur, attrs)
        except sqlite3.Error as e:
            print(e)

    def loadByDay(self, day, attrs):
        try:
            cur = self.conn.cursor()
            cur.execute('SELECT *, strftime(\'%Y%m%d\', date_time) as day, ST_AsBinary(geom) as wkb FROM ' + self.table + ' WHERE day=\'' + day + '\'')
            return self.__fetchSystems(cur, attrs)
        except sqlite3.Error as e:
            print(e)

    def loadByDate(self, format, date, attrs):
        try:
            cur = self.conn.cursor()
            cur.execute('SELECT *, strftime(\'' + format + '\', date_time) as date, ST_AsBinary(geom) as wkb FROM ' + self.table + ' WHERE date=\'' + date + '\'')
            return self.__fetchSystems(cur, attrs)
        except sqlite3.Error as e:
            print(e)

    def load(self, name, attrs):
        try:
            cur = self.conn.cursor()
            cur.execute('SELECT *, ST_AsBinary(geom) as wkb FROM ' + self.table + ' WHERE name=\'' + name + '\'')
            return self.__fetchFamily(cur, attrs)
        except sqlite3.Error as e:
            print(e)

    def execute(self, cmd):
        try:
            cur = self.conn.cursor()
            cur.execute(cmd)
            cur.close()
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def query(self, query):
        try:
            cur = self.conn.cursor()
            cur.execute(query)
            results = cur.fetchall()
            cur.close()
            return results
        except sqlite3.Error as e:
            print(e)

    def __fetchFamily(self, cur, attrs):
        systems = self.__fetchSystems(cur, attrs)
        family = ConvectiveSystemFamily()
        for s in systems:
            family.addSystem(s)

        return family

    def __fetchSystems(self, cur, attrs):
        systems = []
        for row in cur.fetchall():
            # Load geometry and create object
            s = ConvectiveSystem(ogr.CreateGeometryFromWkb(bytes(row['wkb'])))

            # Load numeric attributes
            s.name = uuid.UUID(row['name'])
            s.timestamp = datetime.strptime(str(row['date_time']), '%Y-%m-%d %H:%M:%S')

            for name in attrs:
                s.attrs[name] = row[name]

            # Load relationships
            if row['relationships'] != '':
                relations = row['relationships'].split(' ')
                for name in relations:
                    s.relationships.append(uuid.UUID(name))

            s.event = row['event']

            # Load raster data
            raster = row['raster']
            nodata = row['nodata']

            # Apply mask
            raster = np.ma.masked_where(raster == nodata, raster, False)
            
            s.raster = raster
            if raster.dtype == np.int16:
                s.raster = raster/100.0

            s.nodata = nodata
            s.geotransform = row['geotransform']

            systems.append(s)

        cur.close()

        return systems
