import initExample ## Add path to library (just for examples; you do not need this)

import pyqtgraph as pg
from pyqtgraph.Qt import QtTest
from examples.ExampleApp import ExampleLoader

pg.mkQApp()

def test_ExampleLoader():
    loader = ExampleLoader()
    QtTest.QTest.qWaitForWindowExposed(loader)
    QtTest.QTest.qWait(200)
    loader.close()

if __name__ == "__main__":
    test_ExampleLoader()
    pg.exec()
