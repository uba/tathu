..
    This file is part of TATHU - Tracking and Analysis of Thunderstorms.
    Copyright (C) 2022 INPE.

    TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

==============================================
TATHU - Tracking and Analysis of Thunderstorms
==============================================

.. image:: https://img.shields.io/badge/license-MIT-green
        :target: https://github.com//uba/tathu/blob/master/LICENSE
        :alt: Software License

.. image:: https://readthedocs.org/projects/tathu/badge/?version=latest
        :target: https://tathu.readthedocs.io/en/latest/
        :alt: Documentation Status

.. image:: https://img.shields.io/badge/lifecycle-experimental-orange.svg
        :target: https://www.tidyverse.org/lifecycle/#maturing
        :alt: Software Life Cycle

.. image:: https://img.shields.io/github/tag/uba/tathu.svg
        :target: https://github.com/uba/tathu/releases
        :alt: Release

.. image:: https://img.shields.io/pypi/v/tathu
        :target: https://pypi.org/project/tathu/
        :alt: Python Package Index

About
=====
TATHU is a Python package for tracking and analyzing the life cycle of convective systems.

**Convective Systems (CS)** are defined as an organized ensemble of thunderstorm clusters and are associated with severe weather events and natural disasters (hail, lightning, precipitation extremes, high winds, among others). Thus, several works propose automatic methods for **monitoring** these elements in order to provide, for each individual CS, characteristics that can describe its **spatio-temporal** evolution, i.e. the life cycle.

The package provides a modular and extensible structure, supports different types of geospatial data and proposes the use of **Geoinformatics
techniques** and **spatial databases** in order to aid in the analysis and computational representation of the CS.

Contextualization
=======

CS have a spatio-temporal behavior: they originate in a specific geographic location and change over time in relation to position, size and microphysical composition. We may use **remote sensing data**, such as satellite imagery and radar data, in order to **identifying**, **tracking**, **analyzing** and **nowcasting** the CS evolution.

.. image:: https://github.com/uba/tathu/raw/master/docs/sphinx/img/system-evolution-en.jpg
    :target: https://github.com/uba/tathu/raw/master/docs/sphinx/img/system-evolution-en.jpg
    :width: 600
    :alt: CS and spatio-temporal behavior.

The general steps involved for automatic monitoring the CS are:

.. image:: https://github.com/uba/tathu/raw/master/docs/sphinx/img/tracking-methodology-en.jpg
    :target: https://github.com/uba/tathu/raw/master/docs/sphinx/img/tracking-methodology-en.jpg
    :width: 800
    :alt: Tracking methodology.
    
* **Observation**: data acquisition from specific instrumentation. For example, digital images obtained from satellites of geostationary or polar orbit, measurements of meteorological RADAR, among other sources;
* **Detection**: step to identify the objects of interest existing in the observed data. In the specific case of digital images, the use of different processing techniques can be considered, such as: thresholding, segmentation, classification, filters, among others.
* **Description**: extraction of different types of attributes and classification. In this case, one can consider spectral attributes (measurements of a sensor in different channels), statistical analysis (mean, variance, etc.) and shape characteristics (size, orientation, rectangularity, among others);
* **Tracking**: includes detection and description steps followed by an association process. The objective is to determine the behavior and evolution of the objects of interest, as well as the appearance of new objects;
* **Forecast**: based on specialized knowledge (models and parameterization) and the history of each object, it aims to predict what will be the behavior for future moments.

Model
=====
TATHU proposes a conceptual model to address the problem of tracking and analyzing the CS lifecycle.

The entities of the model are:

.. image:: https://github.com/uba/tathu/raw/master/diagrams/tathu-diagram-entities.png
    :target: https://github.com/uba/tathu/raw/master/diagrams/tathu-diagram-entities.png
    :width: 600
    :alt: Entities.

Basically, a geospatial database contains the observed elements of interest, represented by the ``ConvectiveSystem`` class.
This class has at least one spatial attribute, ``geom``, which indicates the geographic limits of the system, and n other attributes, ``fields``.
Thus, four different entities are used:

* **Detector**: interface for detecting the CS present at a given time. This interface takes an image as parameter and should return a ``list`` of ``ConvectiveSystem`` as a result. For each element, the ``geom`` attribute is defined. As an example, detection can be performed from a thresholding operation, i.e. ``ThresholdDetector``;
* **Descriptor**: responsible for the characterization of CS. This entity defines, for each system, a list of **descriptive attributes**. It receives as parameters auxiliary data and a ``list`` of ``ConvectiveSystem``. For example, calculating statistical attributes such as mean, minimum and maximum temperatures - ``StatisticalDescriptor``;
* **Tracker**: this interface aims to tracking the SC (i.e. **associate in time** the different elements detected in each observation). The abstract method takes as parameters two ``lists`` containing ``ConvectiveSystem`` of different time instants - ``previous`` and ``current``. As an example, the association can be performed from the topological relationship between the CS and the analysis of the intersection areas - ``OverlapAreaTracker``;
* **Forecaster**: this interface is built to provide predictions for the CS. One option is to consider a conservative movement, based only on the current speed of the system - ``ConservativeForecaster``.

Installation
=======

Documentation
=======

References
=======

License
=======

.. admonition::
    Copyright (C) 2022 INPE.

    TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.
