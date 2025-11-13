#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

'''Fortracc - Implementation of the ForTraCC methodology using the TATHU package.'''

import glob
import warnings
from osgeo import gdal
from shapely.errors import ShapelyDeprecationWarning

from tathu.constants import LAT_LON_WGS84
from tathu.io import spatialite
from tathu.satellite import goes_r
from tathu.tracking import descriptors, detectors, trackers
from tathu.tracking.utils import area2degrees
from tathu.utils import file2timestamp

warnings.filterwarnings('ignore', category=ShapelyDeprecationWarning)

class Fortracc:
    '''
    Implements the ForTraCC (Forecasting and Tracking of Cloud Clusters) methodology
    using the TATHU framework.

    The ForTraCC technique was developed to detect, track and forecast the
    evolution of mesoscale convective cloud clusters using geostationary satellite
    infrared imagery (e.g., 10.8 µm channel).
    The method involves threshold-based detection of cold cloud tops,
    statistical description of clusters, overlap-based tracking across successive images,
    and calculation of motion/area-growth attributes to support forecasting of cluster
    behaviour (e.g., displacement, expansion, decay). [Machado & Laurent 2007]
    Reference:
    Machado, L. A. T., Laurent, H., et al. (2007). “Forecast and Tracking the Evolution of Cloud Clusters (ForTraCC)
    using infrared imagery: Methodology and Validation.” *Weather and Forecasting*, 23(2).
    Link: https://journals.ametsoc.org/view/journals/wefo/23/2/2007waf2006121_1.xml
    '''

    def __init__(
        self,
        extent=None,
        resolution=2.0,
        threshold=230,
        min_area_km2=3000,
        overlap_area_criterion=0.1,
        stats_attrs=None,
        movement_attrs=None,
        db_path='systems-db-fortracc.sqlite',
        db_table='systems',
    ):
        # Parameters
        self.extent = extent or [-100.0, -56.0, -20.0, 15.0]
        self.resolution = resolution
        self.threshold = threshold
        self.min_area = area2degrees(min_area_km2)
        self.overlap_area_criterion = overlap_area_criterion

        self.stats_attrs = stats_attrs or ['min', 'mean', 'std', 'median', 'count']
        self.movement_attrs = movement_attrs or ['nae', 'velocity', 'u', 'v', 'direction']

        # Initialize Spatialite output
        self.db = spatialite.Outputter(db_path, db_table, self.stats_attrs + self.movement_attrs)

        # Tracking strategy
        self.strategy = trackers.RelativeOverlapAreaStrategy(self.overlap_area_criterion)

    def detect(self, path):
        '''Detect convective systems in a GOES image.'''
        timestamp = file2timestamp(path, regex=goes_r.DATE_REGEX, format=goes_r.DATE_FORMAT)

        print(f'Processing {timestamp}')

        # Remap to regular grid
        grid = goes_r.sat2grid(
            path,
            self.extent,
            self.resolution,
            LAT_LON_WGS84,
            'HDF5',
            progress=gdal.TermProgress_nocb,
        )

        # Detect cold cloud tops below threshold
        detector = detectors.LessThan(self.threshold, self.min_area)
        systems = detector.detect(grid)

        # Assign timestamps
        for s in systems:
            s.timestamp = timestamp

        # Compute basic statistical descriptors
        descriptor = descriptors.StatisticalDescriptor(stats=self.stats_attrs, rasterOut=True)
        descriptor.describe(grid, systems)

        # Add movement attributes (to be computed later)
        for s in systems:
            s.addAtributes(self.movement_attrs)

        grid = None

        return systems

    def track(self, files):
        '''Run the full detection and tracking sequence on a list of image files.'''
        if not files:
            print('No image files provided.')
            return

        # Detect first timestep
        previous = self.detect(files[0])
        self.db.output(previous)

        # Process subsequent files
        for i in range(1, len(files)):
            current = self.detect(files[i])

            # Track systems
            tracker = trackers.OverlapAreaTracker(previous, strategy=self.strategy)
            tracker.track(current)

            # Compute additional descriptors
            nae_desc = descriptors.NormalizedAreaExpansionDescriptor()
            nae_desc.describe(previous, current)

            move_desc = descriptors.MovementDescriptor()
            move_desc.describe(previous, current)

            # Save results
            self.db.output(current)

            previous = current

        print('Tracking completed successfully.')

    def run(self, image_pattern='./data/noaa-goes16/**/*.nc'):
        '''Convenience method to run ForTraCC over a file pattern.'''
        files = sorted(glob.glob(image_pattern, recursive=True))
        self.track(files)
