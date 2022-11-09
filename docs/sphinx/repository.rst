..
    This file is part of TATHU - Tracking and Analysis of Thunderstorms.
    Copyright (C) 2022 INPE.

    TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.


Repository Organization
=======================


Overview
--------


Following is an overview of the files and folders:


.. table::

    +-----------------------------+--------------------------------------------------------------------------------+
    | Name                        | Description                                                                    |
    +=============================+================================================================================+
    + ``docs/sphinx``             | Sphinx based documentation folder.                                             |
    +-----------------------------+--------------------------------------------------------------------------------+
    + ``examples``                | Python scripts with code examples.                                             |
    +-----------------------------+--------------------------------------------------------------------------------+
    + ``tathu``                   | Source code of TATHU package.                                                  |
    +-----------------------------+--------------------------------------------------------------------------------+
    + ``tathu/downloader``        | Module for downloading data.                                                   |
    +-----------------------------+--------------------------------------------------------------------------------+
    + ``tathu/geometry``          | Module of vector geometry support and related operations.                      |
    +-----------------------------+--------------------------------------------------------------------------------+
    + ``tathu/io``                | Module for Input & Output tracking results.                                    |
    +-----------------------------+--------------------------------------------------------------------------------+
    + ``tathu/radar``             | Module for reading RADAR data.                                                 |
    +-----------------------------+--------------------------------------------------------------------------------+
    + ``tathu/satellite``         | Module for reading satellite data.                                             |
    +-----------------------------+--------------------------------------------------------------------------------+
    + ``tathu/tracking``          | Conceptual Model implementation, including entities and algorithms.            |
    +-----------------------------+--------------------------------------------------------------------------------+
    + ``tests``                   | Unit-tests based on PyTest.                                                    |
    +-----------------------------+--------------------------------------------------------------------------------+
    + ``tools``                   | Set of tools that can be used for tracking; e.g. command-line interfaces.      |
    +-----------------------------+--------------------------------------------------------------------------------+
