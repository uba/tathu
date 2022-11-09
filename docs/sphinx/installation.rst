..
    This file is part of TATHU - Tracking and Analysis of Thunderstorms.
    Copyright (C) 2022 INPE.

    TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.


.. _Installation:

.. include:: ../../INSTALL.rst

Build the Documentation
+++++++++++++++++++++++


You can generate the documentation based on Sphinx with the following command::

    sphinx-build -b html docs/sphinx/ docs/build/html/


The above command will generate the documentation in HTML and it will place it under::

    docs/build/html/


You can open the above documentation in your favorite browser, as::

    firefox docs/build/html/index.html