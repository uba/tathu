..
    This file is part of TATHU - Tracking and Analysis of Thunderstorms.
    Copyright (C) 2022 INPE.

    TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Installation
============

We recommend `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_  and ``conda-forge`` channel to install necessary dependencies and use the TATHU package.

Add ``conda-forge`` channel and adjust ``channel_priority`` to ``strict``::

    conda config --add channels conda-forge
    conda config --set channel_priority strict

Clone the TATHU Repository::

    git clone https://github.com/uba/tathu.git
    
Go to the source code folder::

    cd tathu
    
Create a new environment with all necessary dependencies::

    conda env create -f env.yml
    
