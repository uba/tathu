#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Optical Flow Visualizer
__author__ = "Douglas Uba"

import glob

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

from tathu.constants import LAT_LONG_WGS84_BRAZIL_NORTH_EXTENT
from tathu.satellite import goes13
from tathu.utils import readFLO

extent = LAT_LONG_WGS84_BRAZIL_NORTH_EXTENT

# Input images
image_dir = '../../data/goes13-dissm/*.gz'
image_files = sorted(glob.glob(image_dir))

# Read images
images = []
for file in image_files:
    print('Reading', file)
    images.append(goes13.sat2grid(file, extent).ReadAsArray())

# Flow vector files
uv_dir = '*.flo'
uv_files = sorted(glob.glob(uv_dir))

# Dimension
w, h = 0, 0

# Read flow vectors
us, vs = [], []
for file in uv_files:
    print('Reading', file)
    w,h,u,v = readFLO(file)
    us.append(u)
    vs.append(v)
    
# Create grid
x, y = np.meshgrid(np.arange(0, w, 1), np.arange(0, h, 1))

# Create figure
fig = plt.figure()

# Plot first image
im = plt.imshow(images[0], cmap='Greys')

# Reduce factor for vectors
n = 16

# Reduce grid
x = x[::n,::n]
y = y[::n,::n]

# Reduce flow vectors 
for i in range(len(uv_files)):
    us[i] = us[i][::n,::n]
    vs[i] = vs[i][::n,::n]
    
# Plot first vectors
Q = plt.quiver(x, y, us[0], vs[0], pivot='mid', color='dodgerblue',
        angles='xy', headlength=4, antialiased=True, alpha=0.8)

# Animation loop
i = 1
def updatefig(*args):
    global i
    im.set_array(images[i])
    Q.set_UVC(us[i-1], vs[i-1])
    i += 1
    if i == len(images):
        i = 1
    return im
    
anim = animation.FuncAnimation(fig, updatefig, interval=300, blit=False, frames=len(images))
plt.show()
