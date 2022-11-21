..
    This file is part of TATHU - Tracking and Analysis of Thunderstorms.
    Copyright (C) 2022 INPE.

    TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.


Split and Merge
===============

In the tracking process using the area overlapping method (`OverlapAreaTracker <https://github.com/uba/tathu/blob/5a49b11f5d901aba3167bf563bb836860d4696b1/tathu/tracking/trackers.py#L133>`_), TATHU is able to define split and merge events for CS. The ``ConvectiveSystem`` class has an attribute to indicate these events - ``event``. In total, 5 types are considered:

.. figure:: https://raw.githubusercontent.com/uba/tathu/master/docs/sphinx/img/system-events.png
    :target: https://raw.githubusercontent.com/uba/tathu/master/docs/sphinx/img/system-events.png
    :width: 500

    CS events:  (a) continuity, (b) split and (c) merge. The dashed lines represent the systems at time t − ∆t. Adapted from Vila et al. (2008) [#]_.

#. **Spontaneous Generation**: the CS is identified in one image, however, it is not present in the previous image or does not meet the minimum area overlapping criterion. This is the default event;
#. **Natural Dissipation**: It's the end of the system's lifecycle, not identified or tracked in the current image;
#. **Continuity**: the CS is identified in an image and is present in the previous image, i.e. meets the minimum area overlap criterion;
#. **Split**: at time t, there is an CS that satisfies the minimum area overlap criterion with **two** or **more** systems at time t − ∆t;
#. **Merge**: at time t − ∆t, there are **two** or more CS that obey the minimum area overlap criterion with **only one** system at time t.

Computationally:

.. code:: python

    class LifeCycleEvent(Enum):
        '''
        Enumeration that represents the life cycle events of convective systems.
        '''
        SPONTANEOUS_GENERATION = 0
        NATURAL_DISSIPATION = 1
        CONTINUITY = 2
        SPLIT = 3
        MERGE = 4

    class ConvectiveSystem(object):
        def __init__(self, geom):
            # (...)
            self.event = LifeCycleEvent.SPONTANEOUS_GENERATION

After the tracking process, each instant of time will have an associated description of the event. We can list these events from an SQL query, for example:

.. code:: sql

    SELECT event, date_time FROM systems WHERE name='2f790224-9146-400c-b9c6-e11b685d4a3e';

Result:

.. table::

    +------------------------+---------------------+
    | **event**              | **date_time**       |
    +------------------------+---------------------+
    | SPONTANEOUS_GENERATION | 2017-04-08 01:30:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 02:00:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 02:30:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 03:00:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 03:30:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 04:00:00 |
    +------------------------+---------------------+
    | MERGE                  | 2017-04-08 04:30:00 |
    +------------------------+---------------------+
    | MERGE                  | 2017-04-08 05:30:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 06:00:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 06:30:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 07:00:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 07:30:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 08:00:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 08:30:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 09:00:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 09:30:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 10:00:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 10:30:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 11:00:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 11:30:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 12:00:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 12:30:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 13:00:00 |
    +------------------------+---------------------+
    | MERGE                  | 2017-04-08 13:30:00 |
    +------------------------+---------------------+
    | SPLIT                  | 2017-04-08 14:00:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 14:30:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 15:00:00 |
    +------------------------+---------------------+
    | CONTINUITY             | 2017-04-08 16:00:00 |
    +------------------------+---------------------+

.. rubric:: Footnotes

.. [#] Vila, D. A., Machado, L. A. T., Laurent, H., & Velasco, I. (2008). Forecast and Tracking the Evolution of Cloud Clusters (ForTraCC) using satellite infrared imagery: Methodology and validation. Weather and Forecasting, 23(2), 233-245. `<https://journals.ametsoc.org/view/journals/wefo/23/2/2007waf2006121_1.xml>`_.
