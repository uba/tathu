..
    This file is part of TATHU - Tracking and Analysis of Thunderstorms.
    Copyright (C) 2022 INPE.

    TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.


.. _Model:

Conceptual Model
================

TATHU proposes a conceptual model to address the problem of tracking and analyzing the CS lifecycle.

The entities of the model are:

.. figure:: https://github.com/uba/tathu/raw/master/diagrams/tathu-diagram-entities.png
    :target: https://github.com/uba/tathu/raw/master/diagrams/tathu-diagram-entities.png
    :alt: Entities.

    doc-me!

Basically, a geospatial database contains the observed elements of interest, represented by the `ConvectiveSystem <https://github.com/uba/tathu/blob/5a49b11f5d901aba3167bf563bb836860d4696b1/tathu/tracking/system.py#L30>`_ class.
This class has an identifier, ``uuid``, at least one spatial attribute, ``geom``, which indicates the geographic limits of the system, and n other attributes, ``fields``.
Thus, four different entities are used:

Detector
--------

Interface for detecting the CS present at a given time. This interface takes an image as parameter and should return a ``list`` of ``ConvectiveSystem`` as a result. For each element, the ``geom`` attribute is defined. As an example, detection can be performed from a thresholding operation, i.e. `ThresholdDetector <https://github.com/uba/tathu/blob/5a49b11f5d901aba3167bf563bb836860d4696b1/tathu/tracking/detectors.py#L29>`_;

.. code-block:: python

    class Detector(object):
        def __init__(self):
            pass

        def detect(self, image):
            return list(systems)

Descriptor
----------

Responsible for the characterization of CS. This entity defines, for each system, a list of **descriptive attributes**. It receives as parameters auxiliary data and a ``list`` of ``ConvectiveSystem``. For example, calculating statistical attributes such as mean, minimum and maximum temperatures - `StatisticalDescriptor <https://github.com/uba/tathu/blob/5a49b11f5d901aba3167bf563bb836860d4696b1/tathu/tracking/descriptors.py#L22>`_;

.. code-block:: python

    class Descriptor(object):
        def __init__(self):
            pass

        def describe(self, image, systems):
            pass

Tracker
-------

This interface aims to tracking the CS (i.e. **associate in time** the different elements detected in each observation). The abstract method takes as parameters two ``lists`` containing ``ConvectiveSystem`` of different time instants - ``previous`` and ``current``. As an example, the association can be performed from the topological relationship between the CS and the analysis of the intersection areas - `OverlapAreaTracker <https://github.com/uba/tathu/blob/5a49b11f5d901aba3167bf563bb836860d4696b1/tathu/tracking/trackers.py#L133>`_;

.. code-block:: python

    class Tracker(object):
        def __init__(self, previous):
            self.previous = previous

        def track(self, current):
            pass

Forecaster
----------

This interface is built to provide predictions for the CS. One option is to consider a conservative movement, based only on the current speed of the system - `ConservativeForecaster <https://github.com/uba/tathu/blob/5a49b11f5d901aba3167bf563bb836860d4696b1/tathu/tracking/forecasters.py#L60>`_.

.. code-block:: python

    class Forecaster(object):
        def __init__(self, previous, intervals):
            self.previous = previous
            self.intervals = intervals

        def forecast(self, current):
            pass


Pseudocode for detection, characterization, tracking and forecast of CS using the abstract interfaces:

.. code-block:: python

    images = load()
    previous = None
    for each image in images:
        systems = detector.detect(images[i])
        descriptor.describe(systems)
        tracker.track(previous, systems)
        forecaster.forecast(previous, systems)
        previous = systems
