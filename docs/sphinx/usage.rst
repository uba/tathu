..
    This file is part of TATHU - Tracking and Analysis of Thunderstorms.
    Copyright (C) 2022 INPE.

    TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.


Usage
=====

Detection and Tracking Example
------------------------------

The set of code snippet below shows how to use the concepts proposed by TATHU package to identify and track CS using satellite imagery (GOES-16).

Use a netCDF file with values measured by ABI/GOES-16, Channel 13, on June 15, 2021 - 00:00 UTC. A geographic region of interest (extent) and a spatial resolution are defined. The remapping is performed from the original satellite projection to a regular grid, with a LatLon/WGS84 coordinate system (EPSG:4326).

.. code-block:: python

    from tathu.constants import LAT_LON_WGS84
    from tathu.satellite import goes16

    # Path to netCDF GOES-16 file (IR-window) - ("past")
    path = './data/goes16/ch13/2021/06/ch13_202106150000.nc'

    # Geographic area of regular grid
    extent = [-100.0, -56.0, -20.0, 15.0]

    # Grid resolution (kilometers)
    resolution = 2.0

    # Remap
    grid = goes16.sat2grid(path, extent, resolution, LAT_LON_WGS84)

Next, let's detect CS followed by the definition of the statistical attributes. Use of ``detectors.LessThan`` and ``descriptors.StatisticalDescriptor``.

.. code-block:: python

    from tathu.tracking import detectors
    from tathu.tracking import descriptors

    # Threshold value
    threshold = 230 # Kelvin

    # Define minimum area
    minarea = 3000 # km^2

    # Create detector
    detector = detectors.LessThan(threshold, minarea)

    # Detect systems
    systems = detector.detect(grid)

    # Create statistical descriptor
    attrs = ['min', 'mean', 'std', 'count']
    descriptor = descriptors.StatisticalDescriptor(stats=attrs)

    # Describe systems (stats)
    descriptor.describe(grid, systems)

Export the result to a CSV file ``systems.csv``:

.. code-block:: python

    from tathu.io import icsv
    outputter = icsv.Outputter('systems.csv', writeHeader=True)
    outputter.output(systems)

File preview. Each line represents an CS, which has a unique identifier, the date and other attributes::

    name,timestamp,event,min,mean,count,std
    c55f99b4-84a4-4b4b-8393-25aaaf85fb75,2022-06-15 00:00:20.400000,SPONTANEOUS_GENERATION,201.8952178955078,217.48695598417407,2022,8.098725295979632
    dc616f08-e0cd-4a15-87ed-7becc5ab253a,2022-06-15 00:00:20.400000,SPONTANEOUS_GENERATION,201.8952178955078,216.17461281506226,3293,6.3141480994099926
    ed97d8cc-d4e7-4a52-b686-1763bd0281f1,2022-06-15 00:00:20.400000,SPONTANEOUS_GENERATION,196.67169189453125,219.96122828784118,1209,6.635110324130535
    e57dccdf-cf36-4f41-9160-840f29a9111e,2022-06-15 00:00:20.400000,SPONTANEOUS_GENERATION,218.91778564453125,224.71936994856722,1361,2.728877257772919
    37f1de1a-871b-4b5d-b971-48ddb84cd1ed,2022-06-15 00:00:20.400000,SPONTANEOUS_GENERATION,203.6773681640625,212.5015689699793,966,6.889729660848631
    32a42b28-74a1-4221-912e-c401d9051c88,2022-06-15 00:00:20.400000,SPONTANEOUS_GENERATION,191.32525634765625,209.74939927913496,19976,8.544348809460782

The visualization can be performed based on the following snippet:

.. code-block:: python

    from tathu.tracking.visualizer import MapView

    # Create MapView component
    m = MapView(extent)

    # Plot grid
    m.plotImage(grid, cmap='Greys', vmin=180.0, vmax=320.0)

    # Plot systems
    m.plotSystems(systems, edgecolor='red', centroids=True)

    # Show GUI result
    m.show()

.. image:: https://github.com/uba/tathu/raw/master/docs/sphinx/img/map-view.png
    :target: https://github.com/uba/tathu/raw/master/docs/sphinx/img/map-view.png
    :alt: Map view component.

The same result can be exported to a database instance with geospatial support, like SpatiaLite and PostGIS:

.. code-block:: python

    from tathu.io import spatialite
    database = spatialite.Outputter('systems.sqlite', 'systems')
    database.output(systems)

Once the CS present in the image of June 15, 2021 - 00:00 UTC have been detected, it is now possible to perform the tracking. We use a new image, from the same day, 00:10 UTC. Use of ``trackers.OverlapAreaTracker``.

.. code-block:: python

    # Path to new netCDF GOES-16 file - ("present")
    path = './data/goes16/ch13/2021/06/ch13_202106150010.nc'

    # Remap
    grid = goes16.sat2grid(path, extent, resolution, LAT_LON_WGS84)

    # Tracking
    previous = systems

    # Detect new systems
    systems = detector.detect(grid)

    from tathu.tracking import trackers

    # Define overlap area criterion
    overlapAreaCriterion = 0.1 # 10%

    # Create overlap area strategy
    strategy = trackers.RelativeOverlapAreaStrategy(overlapAreaCriterion)

    # Create tracker entity
    t = trackers.OverlapAreaTracker(previous, strategy=strategy)
    t.track(current)

    # Save to database
    database.output(systems)

Finally, the prediction of CS for future moments can be performed based on the following code fragment. Use of ``forecasters.Conservative``.

.. code-block:: python

    from tathu.tracking import forecasters

    times = [15, 30, 45, 60, 90, 120] # minutes

    # Forecaster entity
    f = forecasters.Conservative(previous, intervals=times)

    # Forecast result for each time
    forecasts = f.forecast(current)

Considering that the different CS were detected and stored, the load process can be performed based on the following code snippet:

.. code-block:: python

    from tathu.io import spatialite

    # Setup informations to load systems from database
    dbname = 'systems.sqlite'
    table = 'systems'

    # Connect to database
    db = spatialite.Loader(dbname, table)

    # Get all-systems names
    names = db.loadNames()

    # Load first system, geometry and attributes
    family = db.load(names[0], ['min', 'mean', 'std', 'count'])

Other methods can be used to load CS more efficiently, for example: from the duration time, considering a day or a date range, based on a spatial restriction, among others. For more specific cases, it is also possible to perform a query directly to the database using SQL language.

.. code-block:: python

    # Load CS with life-cycle time-duration >= 10 hours
    systems = db.loadByDuration(10, operator='>=')

    # Load CS with life-cycle time-duration < 1 hours
    systems = db.loadByDuration(1, operator='<')

    # Load CS from day 26/06/2021
    systems = db.loadByDay('20210626')

      # Load CS using SQL query
    systems = db.query('generic query example')

The CS lifecycle can be visualized, where each plot represents an instant of time in the systems life cycle.

.. code-block:: python

    from tathu.tracking import visualizer
    view = visualizer.SystemHistoryView(family)
    view.show()

.. image:: https://github.com/uba/tathu/raw/master/docs/sphinx/img/system-life-cycle-view.png
    :target: https://github.com/uba/tathu/raw/master/docs/sphinx/img/system-life-cycle-view.png
    :width: 800
    :alt: CS lifecycle view.

🛰️ Using GOES-16/ABI Data
--------------------------

TATHU package provides specific modules for downloading, reading and remapping data obtained from the GOES-16 satellite - ``tathu.downloader.goes`` and ``tathu.satellite.goes16``.

The data is downloaded directly from the AWS public service. More info access `NOAA Geostationary Operational Environmental Satellites (GOES) 16, 17 & 18 <https://registry.opendata.aws/noaa-goes/>`_.

You can download all 16 spectral channels provided by the ABI (Advanced Baseline Imager). Specifically, for detecting convective systems, the Channel 13 is generally used, at 10.3 µm.

Example:

.. code-block:: python

    from tathu.downloader.goes import AWS

    # Download data from 08 April 2022, Channel 13, [00, 01, 02, 03] hours UTC
    start = end = datetime.strptime('20220408', '%Y%m%d')
    hours = ['00', '01', '02', '03']

    # From AWS (full-disk)
    AWS.download(AWS.buckets['GOES-16'], ['ABI-L2-CMIPF'],
        start, end, hours, ['13'], './goes16-aws',
        progress=TqdmProgress('Download GOES-16 data (AWS)', 'files'))

The images are in the original acquisition projection, in the full-disk sector. In this case, you can use another module to perform the remapping to a regular grid and then start the object detection and tracking processes. For remapping, you need to provide the desired geographic region and the spatial resolution (in kilometers).

Use the ``extent`` parameter, i.e. a list of four values indicating the lower left (``ll``) and upper right (``ur``) corners coordinates. The correct order of ``extent`` values is:

.. code-block:: python

    extent = [llx, lly, urx, ury]

Example:

.. code-block:: python

    from tathu.constants import LAT_LON_WGS84
    from tathu.satellite import goes16

    # Path to netCDF GOES-16 file
    path = './noaa-goes16/ABI-L2-CMIPF/2022/098/00/ \
        OR_ABI-L2-CMIPF-M6C13_G16_s20220980000203_e20220980009522_c20220980010009.nc'

    # Geographic area of regular grid
    extent = [-100.0, -56.0, -20.0, 15.0]

    # Grid resolution (kilometers)
    resolution = 2.0

    # Remap
    grid = goes16.sat2grid(path, extent, resolution, LAT_LON_WGS84)

🛰️ Using GOES-16/GLM Data
--------------------------

.. warning::

    doc-me!

🛰️ Using GOES-13 Data
---------------------

TATHU also provides specific modules for downloading and reading data obtained from the old `GOES-13 satellite <https://space.oscar.wmo.int/satellites/view/goes_13>`_ - ``tathu.downloader.goes`` and ``tathu.satellite.goes13``.

The data is downloaded directly from the Division of Satellites and Meteorological Sensors, National Institute for Space Research (DISSM/INPE). More info access `DISSM/INPE <http://satelite.cptec.inpe.br/home/index.jsp>`_.

You can download all 5 spectral channels provided by the GOES-13 Imager. Specifically, for detecting convective systems, the Channel 04 is generally used, at 10.7 µm.

Example:

.. code-block:: python

    from tathu.downloader.goes import DISSM

    # Download data from 08 April 2015, Channel 04, [00, 01, 02, 03] hours UTC
    start = end = datetime.strptime('20150408', '%Y%m%d')
    hours = ['00', '01', '02', '03']

    # From DISSM (crop/remapped version - GOES-13)
    DISSM.download('goes13', 'retangular_4km/ch4_bin',
        start, end, hours,
        './goes13-dissm/',
        progress=TqdmProgress('Download GOES-13 data (DISSM/INPE)', 'files'))

.. note::

    For the GOES-13 satellite, the data was pre-processed (i.e. clipped and remapped) by DISSM/INPE. Therefore, it is not necessary to perform the remapping operation for object detection and tracking.

🛰️ Using Meteosat Data
-----------------------

.. warning::

    doc-me!

📡 Using RADAR Data
--------------------

.. warning::

    doc-me!

🤓 Using Your Own Data
----------------------

TATHU package uses the `GDALDataset <https://gdal.org/doxygen/classGDALDataset.html>`_ class from the GDAL library as an abstraction layer for 2D array data, i.e. raster data.

Thus, to use your own data in the detection/tracking process you must be able to read the array of values from your data to an object of type `numpy array <https://numpy.org/doc/stable/reference/generated/numpy.array.html>`_.

Then use the utility method provided by TATHU package - ``array2raster`` - to get a GDALDataset object. This method is defined in the `tathu/utils.py <https://github.com/uba/tathu/blob/master/tathu/utils.py>`_ file.

You must also inform in which geographic region the data is located. This is possible from the ``extent`` parameter, i.e. a list of four values indicating the lower left (``ll``) and upper right (``ur``) corners coordinates. The correct order of ``extent`` values is:

.. code-block:: python

    extent = [llx, lly, urx, ury]

Example:

.. code-block:: python

    from tathu.utils import array2raster

    # Read your data to 2D numpy array
    array = your_method_to_read_your_data_to_numpy_array()

    # Define the geographic extent in format [llx, lly, urx, ury]. Example:
    extent = [-100.0, -56.0, -20.0, 15.0]

    # Use TATHU array2raster method
    raster = array2raster(array, extent)

    # From here, you can use all methods provided by the package
    # to detect, describe and track objects of interest.
    from tathu.tracking import descriptors, detectors

    # Create detector
    detector = detectors.LessThan(threshold, minarea)

    # Detect objects
    objects = detector.detect(raster)

    # Create descriptor
    descriptor = descriptors.StatisticalDescriptor()

    # Describe objects
    descriptor.describe(raster, objects)

    # (...)

That's it! 👍

The ConvectiveSystem Class
--------------------------

The `ConvectiveSystem <https://github.com/uba/tathu/blob/5a49b11f5d901aba3167bf563bb836860d4696b1/tathu/tracking/system.py#L30>`_ class represents an observed and detected CS at a specific instant of time. This class has at least  one spatial attribute, ``geom``, which indicates the geographical limits of the system, n other attributes, ``fields``, in addition to a unique universal identifier, ``uuid``.

.. note::

    TATHU uses the **vector representation** for the computational manipulation of CS, which has advantages over the raster representation:

    #. Spatial indexing using structures of tree data type, R-tree [#]_;
    #. Efficient application of set and topological operators [#]_;
    #. Read the pixels of each CS using efficient iterators;
    #. Ability to use geometric transformations [#]_.

The vector representation has open standards specified for storing and exchanging this type of data, for example: SFS - Simple Feature Access [#]_, WKT - Well-Known Text [#]_, WKB - Well-Known Binary [#]_ and files like GeoJSON and ESRI Shapefile, etc.

It is possible to use a database with spatial support (like `PostGIS <https://postgis.net/>`_ or `SpatiaLite <https://www.gaia-gis.it/fossil/libspatialite/index>`_) in order to store the convective system objects. These databases have the ability to store tabular attributes together with the spatial representation of objects, allowing the construction of different functionalities and query modes. Storing the results in this type of structure, it is possible to perform space temporal queries efficiently. As an example, consider the following hypothetical scenarios, common in CS analysis and applications. All of them can be efficiently answered with this approach.

    * > *Recover the CS detected in the South/Southeast regions of Brazil in the period from 01/01/2020 to 04/08/2021;*
    * > *Get the CS detected in the North region of Brazil whose area is greater than N km2;*
    * > *How many CS occurred in a given time interval and in a given geographic region?*
    * > *What is the average lifetime of CS? etc.*

As an example, the last question can be answered from the following SQL command:

.. code-block:: sql

    -- What is the average lifetime of CS?
    SELECT AVG(elapsed_time)
    FROM (SELECT name, (MAX(julianday(date_time)) - MIN(julianday(date_time))) * 24 AS elapsed_time
    FROM systems GROUP BY(name)) duration;

Tracking Input & Output
-----------------------

Module for reading and writing the data obtained from the CS tracking process. This module offers option to
various formats and storage modes, including different file types (e.g. CSV, ESRI Shapefile, KML, GeoJSON, etc.) and database with spatial support (e.g. `PostGIS <https://postgis.net/>`_ or `SpatiaLite <https://www.gaia-gis.it/fossil/libspatialite/index>`_). The implementations are based on two interfaces: ``Loader`` and ``Outputter``.

.. figure:: https://github.com/uba/tathu/raw/master/docs/sphinx/img/tathu-io-diagram.png
    :target: https://github.com/uba/tathu/raw/master/docs/sphinx/img/tathu-io-diagram.png
    :alt: Input & Output interfaces.

|

.. code-block:: python

    class Outputter(object):
        """
        Abstract class can be used to export tracking results.
        """
        def __init__(self):
            pass

        def output(self, systems):
            pass

.. code-block:: python

    class Loader(object):
        """
        Abstract class can be used to load tracking results.
        """
        def __init__(self):
            pass

        def loadNames(self):
            pass

        def loadByDuration(self, hours, operator='>='):
            pass

        def loadByInterval(self, start, end):
            pass

        def loadByDay(self, day, attrs):
            pass

        def query(self, query):
            pass

        # (...)

Example to export the result to a CSV file called ``systems.csv``:

.. code-block:: python

    from tathu.io import icsv
    outputter = icsv.Outputter('systems.csv', writeHeader=True)
    outputter.output(systems)

Example to export the result to ESRI Shapefile called ``systems.shp``:

.. code-block:: python

    from tathu.io import vector
    outputter = vector.Shapefile('systems.shp')
    outputter.output(systems)

Example to export the result to GeoJSON file called ``systems.json``:

.. code-block:: python

    from tathu.io import vector
    outputter = vector.GeoJSON('systems.json')
    outputter.output(systems)

Example to export the result to SpatiaLite database called ``systems-db.sqlite``:

.. code-block:: python

    from tathu.io import spatialite
    # Create database connection
    db = spatialite.Outputter('systems-db.sqlite', 'systems', attrs)
    # Save to database
    db.output(systems)

.. rubric:: Footnotes

.. [#] GUTTMAN, A. R-trees: A dynamic index structure for spatial searching. SIGMOD Rec., Association for Computing Machinery, New York, NY, USA, v. 14, n. 2, p. 4757, jun 1984. ISSN 0163-5808. `Link <https://doi.org/10.1145/971697.602266>`_.
.. [#] PostGIS Reference: `Topological Relationships <https://postgis.net/docs/reference.html#idm12212>`_ and `Overlay Functions <https://postgis.net/docs/reference.html#Overlay_Functions>`_.
.. [#] PostGIS Reference: `Affine Transformations <https://postgis.net/docs/reference.html#Affine_Transformation>`_.
.. [#] HERRING, J. et al. Opengis® implementation standard for geographic information - simple feature access - part 1: Common architecture [corrigendum]. Open Geospatial Consortium, 2011.
.. [#] Well-known text (WKT) representation of geometry  - `<https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry>`_.
.. [#] Well-known binary (WKB) representation of geometry  - `<https://www.ibm.com/docs/en/db2/11.5?topic=formats-well-known-binary-wkb-representation>`_.
