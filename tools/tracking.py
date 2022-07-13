#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import configparser
import glob
import os
import sys

import click

from tathu.constants import KM_PER_DEGREE, LAT_LON_WGS84
from tathu.io import spatialite
from tathu.satellite import goes16
from tathu.tracking import descriptors, detectors, trackers
from tathu.utils import Timer, extractPeriods, file2timestamp

def getFiles(basedir):
    search = os.path.join(basedir, '**/*.nc')
    print('Searching files', search)
    files = sorted(glob.glob(search, recursive=True))
    return files

def detect(path, date_regex, date_format, extent, resolution, threshold,
    minarea, stats, threshold_cc, minarea_cc):
    with Timer():
        # Extract file timestamp
        timestamp = file2timestamp(path, date_regex, date_format)
        
        print('Searching for systems at:', timestamp)

        # Remap channel to 2km
        grid = goes16.sat2grid(path, extent, resolution, LAT_LON_WGS84, 'HDF5', progress=None)

        # Create detector
        detector = detectors.LessThan(threshold, minarea)

        # Searching for systems
        systems = detector.detect(grid)

        # Adjust timestamp
        for s in systems:
            s.timestamp = timestamp
            
        # Create statistical descriptor
        descriptor = descriptors.StatisticalDescriptor(stats=stats, rasterOut=True)
        
        # Describe systems (stats)
        systems = descriptor.describe(grid, systems)

        # Create convective cell descriptor
        descriptor = descriptors.ConvectiveCellsDescriptor(threshold_cc, minarea_cc)

        # Describe systems (convective cell)
        descriptor.describe(grid, systems)

        # Add normalized area expansion attribute
        for s in systems:
            s.attrs['nae'] = 0

        grid = None

        return systems

def track(files, date_regex, date_format, extent, resolution, threshold, minarea,
    stats, threshold_cc, minarea_cc, areaoverlap, outputter):
    try:
        img = 0
        # Detect first systems
        current = detect(files[img], date_regex, date_format, extent, resolution, threshold,
            minarea, stats, threshold_cc, minarea_cc)

        # Save to output
        outputter.output(current)
        img = img + 1

        # Prepare tracking...
        previous = current

        # Create overlap area strategy
        strategy = trackers.RelativeOverlapAreaStrategy(areaoverlap)

        # for each image file
        for i in range(img, len(files)):
            # Detect current systems
            current = detect(files[i], date_regex, date_format, extent, resolution,
                threshold, minarea, stats, threshold_cc, minarea_cc)
            
            # Let's track!
            t = trackers.OverlapAreaTracker(previous, strategy=strategy)
            t.track(current)
            
            # Compute normalized area expansion attribute, if requested
            descriptor = descriptors.NormalizedAreaExpansionDescriptor()
            descriptor.describe(previous, current)

            # Save to output
            outputter.output(current)
            
            # Prepare next iteration
            previous = current
    except Exception as e:
        print('Unexpected error:', e, sys.exc_info()[0])
        
@click.command()
@click.option('--config', type=click.Path(exists=True), help='Path to config tracking file.', required=True)
def main(config):
    # Read config file and extract infos
    params = configparser.ConfigParser(interpolation=None)
    params.read(config)

    # Get extent
    extent = [float(i) for i in params.get('grid', 'extent').split(',')]

    # Get resolution
    resolution = float(params.get('grid', 'resolution'))

    # Get input-data parameters
    repository = params.get('input', 'repository')
    date_regex = params.get('input', 'date_regex')
    date_format = params.get('input', 'date_format')

    # Get tracking parameters
    timeout = float(params.get('tracking_parameters', 'timeout'))
    threshold = float(params.get('tracking_parameters', 'threshold'))
    minarea = float(params.get('tracking_parameters', 'minarea'))
    areaoverlap = float(params.get('tracking_parameters', 'areaoverlap'))
    stats = [i.strip() for i in params.get('tracking_parameters', 'stats').split(',')]

    # Get tracking parameters related with convective cells
    threshold_cc = float(params.get('tracking_parameters', 'threshold_cc'))
    minarea_cc = float(params.get('tracking_parameters', 'minarea_cc'))

    # Output
    database = params.get('output', 'database')

    # Columns
    columns = stats.copy()
    columns.append('nae')
    columns.append('ncells')
    
    # Get files
    files = getFiles(repository)

    if not files:
        print('* Tracking exit: No images found.')
        exit(0)

    # Get date range
    date_start = date_end = file2timestamp(files[0], date_regex, date_format)
    if len(files) > 1:
        date_end = file2timestamp(files[-1], date_regex, date_format)

    # Print infos
    print('== Tathu - Tracking and Analysis of Thunderstorms ==')
    print(':: Start Date:', date_start)
    print(':: End Date:', date_end)
    print(':: Config tracking file location:', config)
    print(':: Extent:', extent)
    print(':: Grid Resolution:', resolution, 'km')
    print(':: Repository of images:', repository)
    print(':: Date Regex:', date_regex)
    print(':: Date Format:', date_format)
    print(':: Minimum accepted time interval between two images:', timeout, 'minutes')
    print(':: Brightness temperature threshold:', threshold, 'K')
    print(':: Minimum area of systems:', minarea, 'km2')
    print(':: Area Overlap:', areaoverlap * 100, '%')
    print(':: Stats:', stats)
    print(':: CC temperature threshold:', threshold_cc, 'K')
    print(':: Minimum area of CC:', minarea_cc, 'km2')

    # Convert to degrees^2
    minarea = minarea/(KM_PER_DEGREE * KM_PER_DEGREE)
    minarea_cc = minarea_cc/(KM_PER_DEGREE * KM_PER_DEGREE)

    # Extracting periods
    periods = extractPeriods(files, timeout, date_regex, date_format)

    # Create database connection
    db = spatialite.Outputter(database, 'systems', columns)

    # Tracking
    for period in periods:
        track(period, date_regex, date_format, extent, resolution,
            threshold, minarea, stats, threshold_cc, minarea_cc, areaoverlap, db)

if __name__ == '__main__':
    main()
