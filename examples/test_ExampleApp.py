import initExample ## Add path to library (just for examples; you do not need this)

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore, mkQApp, QtTest


from examples.ExampleApp import ExampleLoader

def test_ExampleLoader():
    app = pg.mkQApp()
    loader = ExampleLoader()
    QtTest.QTest.qWaitForWindowExposed(loader)
    QtTest.QTest.qWait(200)
    loader.close()

if __name__ == "__main__":
    test_ExampleLoader()
    pg.exec()
