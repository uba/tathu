#!/usr/bin/env bash
#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

pydocstyle tathu examples tests setup.py && \
isort tathu examples tests setup.py --check-only --diff && \
check-manifest --ignore ".readthedocs.yml" && \
sphinx-build -qnW --color -b doctest docs/sphinx/ docs/sphinx/_build/doctest && \
pytest
