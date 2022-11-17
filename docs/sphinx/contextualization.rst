..
    This file is part of TATHU - Tracking and Analysis of Thunderstorms.
    Copyright (C) 2022 INPE.

    TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.


.. _Contextualization:

Contextualization
=================

CS have a spatio-temporal behavior: they originate in a specific geographic location and change over time in relation to position, size and microphysical composition. We may use **remote sensing data**, such as satellite imagery and radar data, in order to **identifying**, **tracking**, **analyzing** and **nowcasting** the CS evolution.

.. figure:: https://github.com/uba/tathu/raw/master/docs/sphinx/img/system-evolution-en.jpg
    :target: https://github.com/uba/tathu/raw/master/docs/sphinx/img/system-evolution-en.jpg
    :width: 600
    :alt: CS and spatio-temporal behavior.

    CS and spatio-temporal behavior.

.. figure:: https://github.com/uba/tathu/raw/master/docs/sphinx/img/goes16-cs-example.gif
    :target: https://github.com/uba/tathu/raw/master/docs/sphinx/img/goes16-cs-example.gif
    :width: 300
    :alt: GOES16 example.

    GOES-16 satellite imagery showing the evolution of a CS.

The general steps involved for automatic monitoring the CS are:

.. figure:: https://github.com/uba/tathu/raw/master/docs/sphinx/img/tracking-methodology-en.jpg
    :target: https://github.com/uba/tathu/raw/master/docs/sphinx/img/tracking-methodology-en.jpg
    :width: 800
    :alt: Tracking methodology.

    Tracking and Analysis methodology.

* **Observation**: data acquisition from specific instrumentation. For example, digital images obtained from satellites of geostationary or polar orbit, measurements of meteorological RADAR, among other sources;
* **Detection**: step to identify the objects of interest existing in the observed data. In the specific case of digital images, the use of different processing techniques can be considered, such as: thresholding, segmentation, classification, filters, among others.
* **Description**: extraction of different types of attributes and classification. In this case, one can consider spectral attributes (measurements of a sensor in different channels), statistical analysis (mean, variance, etc.) and shape characteristics (size, orientation, rectangularity, among others);
* **Tracking**: includes detection and description steps followed by an association process. The objective is to determine the behavior and evolution of the objects of interest, as well as the appearance of new objects;
* **Forecast**: based on specialized knowledge (models and parameterization) and the history of each object, it aims to predict what will be the behavior for future moments.


