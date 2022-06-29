#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

from tqdm import tqdm

class TqdmProgress:
    def __init__(self, title, unit):
        self.title = title
        self.unit = unit
        self.progressBar = None
    def startTask(self, size):
        self.progressBar = tqdm(desc=self.title, total=size, unit=self.unit)
    def startStep(self, text):
        pass
    def endStep(self, text):
        self.progressBar.update()
    def endTask(self):
        pass
    def wasCanceled(self):
        return False
