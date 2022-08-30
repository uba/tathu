#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np

class Envelope(object):
    '''
    An Envelope defines a 2D rectangular region.
    '''
    def __init__(self, llx=np.finfo(float).max, lly=np.finfo(float).max,
                       urx=np.finfo(float).min, ury=np.finfo(float).min):
        self.llx = llx # Lower left corner x-coordinate.
        self.lly = lly # Lower left corner y-coordinate.
        self.urx = urx # Upper right corner x-coordinate.
        self.ury = ury # Upper right corner y-coordinate.

    def initFromList(self, values):
        self.llx = values[0]
        self.lly = values[1]
        self.urx = values[2]
        self.ury = values[3]

    def makeInvalid(self):
        self.llx = np.finfo().max
        self.lly = np.finfo().max
        self.urx = np.finfo().min
        self.ury = np.finfo().min

    def isValid(self):
        if self.llx <= self.urx and self.lly <= self.ury:
            return True
        else:
            return False

    def getLowerLeftX(self):
        return self.llx

    def getLowerLeftY(self):
        return self.lly

    def getLowerLeft(self):
        return (self.llx, self.lly)

    def getUpperRightX(self):
        return self.urx

    def getUpperRightY(self):
        return self.ury

    def getUpperRight(self):
        return (self.urx, self.ury)

    def getWidth(self):
      return np.abs(self.urx - self.llx)

    def getHeight(self):
      return np.abs(self.ury - self.lly)

    def getCenter(self):
        return (self.llx + (self.urx - self.llx) * 0.5,
                self.lly + (self.ury - self.lly) * 0.5)

    def getArea(self):
      return self.getWidth() * self.getHeight()

    def union(self, e):
        # Adjust lower-left x
        if e.llx < self.llx:
            self.llx = e.llx
        # Adjust lower-left y
        if e.lly < self.lly:
            self.lly = e.lly
        # Adjust upper-right x
        if self.urx < e.urx:
            self.urx = e.urx
        # Adjust upper-right y
        if self.ury < e.ury:
            self.ury = e.ury

    def intersects(self, e):
        if self.urx < e.llx or self.llx > e.urx or self.ury < e.lly or self.lly > e.ury:
            return False
        else:
            return True

    def __str__(self):
        return '[%s, %s, %s, %s]' % (self.llx, self.lly, self.urx, self.ury)

    def intersection(self, e):
        llx = self.llx if self.llx > e.llx else e.llx
        lly = self.lly if self.lly > e.lly else e.lly
        urx = self.urx if self.urx < e.urx else e.urx
        ury = self.ury if self.ury < e.ury else e.ury
        return Envelope(llx, lly, urx, ury)

    def getGraphicalRepresentation(self):
        return patches.Rectangle(self.getLowerLeft(), self.getWidth(), self.getHeight(), alpha=0.1)

    def show(self):
        plt.figure()
        plt.gca().add_patch(self.getGraphicalRepresentation())
        plt.gca().relim()
        plt.gca().autoscale_view()
        plt.show()
