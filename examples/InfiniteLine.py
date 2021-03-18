# -*- coding: utf-8 -*-
"""
This example demonstrates some of the plotting items available in pyqtgraph.
"""

import initExample ## Add path to library (just for examples; you do not need this)
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg


app = pg.mkQApp("InfiniteLine Example")
win = pg.GraphicsLayoutWidget(show=True, title="Plotting items examples")
win.resize(1000,600)

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

# Create a plot with some random data
p1 = win.addPlot(title="Plot Items example", y=np.random.normal(size=100, scale=10), pen=0.5)
p1.setYRange(-40, 40)

# Add three infinite lines with labels
inf1 = pg.InfiniteLine(movable=True, angle=90, label='x={value:0.2f}', 
                       labelOpts={'position':0.1, 'color': (200,200,100), 'fill': (200,200,200,50), 'movable': True})
inf2 = pg.InfiniteLine(movable=True, angle=0, pen=(0, 0, 200), bounds = [-20, 20], hoverPen=(0,200,0), label='y={value:0.2f}mm', 
                       labelOpts={'color': (200,0,0), 'movable': True, 'fill': (0, 0, 200, 100)})
inf3 = pg.InfiniteLine(movable=True, angle=45, pen='g', label='diagonal',
                       labelOpts={'rotateAxis': [1, 0], 'fill': (0, 200, 0, 100), 'movable': True})
inf1.setPos([2,2])
p1.addItem(inf1)
p1.addItem(inf2)
p1.addItem(inf3)

targetItem1 = pg.TargetItem(
    label=True,
    symbol="crosshair",
    labelOpts={
        "angle": 0
    }
)

targetItem2 = pg.TargetItem(
    pos=(30, 5),
    size=20,
    label="vert={1:0.2f}",
    symbol="star",
    pen="#F4511E",
    labelOpts={
        "angle": 45,
        "offset": QtCore.QPoint(15, 15)
    }
)

targetItem3 = pg.TargetItem(
    pos=(10, 10),
    size=10,
    label="Third Label",
    symbol="x", 
    pen="#00ACC1",
    labelOpts={
        "anchor": QtCore.QPointF(0.5, 0.5),
        "offset": QtCore.QPointF(30, 0),
        "color": "#558B2F",
        "rotateAxis": (0, 1)
    }
)

p1.addItem(targetItem1)
p1.addItem(targetItem2)
p1.addItem(targetItem3)

# Add a linear region with a label
lr = pg.LinearRegionItem(values=[70, 80])
p1.addItem(lr)
label = pg.InfLineLabel(lr.lines[1], "region 1", position=0.95, rotateAxis=(1,0), anchor=(1, 1))


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
