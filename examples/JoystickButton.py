# -*- coding: utf-8 -*-
"""
JoystickButton is a button with x/y values. When the button is depressed and the
mouse dragged, the x/y values change to follow the mouse.
When the mouse button is released, the x/y values change to 0,0 (rather like 
letting go of the joystick).
"""

import initExample ## Add path to library (just for examples; you do not need this)

from pyqtgraph.Qt import QtCore, QtWidgets
import pyqtgraph as pg

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        cw = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout()
        cw.setLayout(layout)
        self.setCentralWidget(cw)
        self.resize(300,50)

        self.l1 = pg.ValueLabel(siPrefix=True, suffix='m')
        self.l2 = pg.ValueLabel(siPrefix=True, suffix='m')
        self.jb = pg.JoystickButton()
        self.jb.setFixedWidth(30)
        self.jb.setFixedHeight(30)

        layout.addWidget(self.l1, 0, 0)
        layout.addWidget(self.l2, 0, 1)
        layout.addWidget(self.jb, 0, 2)

        self.x = 0
        self.y = 0

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

    def update(self):
        dx, dy = self.jb.getState()
        self.x += dx * 1e-3
        self.y += dy * 1e-3
        self.l1.setValue(self.x)
        self.l2.setValue(self.y)

app = pg.mkQApp("Joystick Button Example")
mw = MainWindow()
mw.show()


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()
