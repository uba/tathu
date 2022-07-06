..
    This file is part of TATHU - Tracking and Analysis of Thunderstorms.
    Copyright (C) 2022 INPE.

    TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Installation
============

We recommend **Miniconda** and ``conda-forge`` channel to install necessary dependencies and use the TATHU package.

1. First, install  `Miniconda <https://docs.conda.io/en/latest/miniconda.html#latest-miniconda-installer-links>`_.

2. Add ``conda-forge`` channel and adjust ``channel_priority`` to ``strict``::

    conda config --add channels conda-forge
    conda config --set channel_priority strict

3. Clone the TATHU Repository::

    git clone https://github.com/uba/tathu.git
    
4. Go to the source code folder::

    cd tathu
    
5. Create a new environment with all necessary dependencies::

    conda env create -f env.yml
    
6. Active the created environment (``env-tathu``)::

    conda activate env-tathu

7. Install TATHU package::

    python -m pip install --no-deps .
    or
    python -m pip install --no-deps -e . # develop mode
    
8. Verify installation::

    python
    import tathu
    tathu.__version__
    

