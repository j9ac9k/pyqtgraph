# -*- coding: utf-8 -*-
"""
Tests the speed of image updates for an ImageItem and RawImageWidget.
The speed will generally depend on the type of data being shown, whether
it is being scaled and/or converted by lookup table, and whether OpenGL
is used by the view widget
"""

## Add path to library (just for examples; you do not need this)
import initExample

import argparse
import sys

import numpy as np

import pyqtgraph as pg
import pyqtgraph.ptime as ptime
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets, QT_LIB

pg.setConfigOption('imageAxisOrder', 'row-major')

import importlib
ui_template = importlib.import_module(f'VideoTemplate_{QT_LIB.lower()}')

try:
    import cupy as cp
    pg.setConfigOption("useCupy", True)
    _has_cupy = True
except ImportError:
    cp = None
    _has_cupy = False

try:
    from pyqtgraph.widgets.RawImageWidget import RawImageGLWidget
except ImportError:
    RawImageGLWidget = None

parser = argparse.ArgumentParser(description="Benchmark for testing video performance")
parser.add_argument('--cuda', default=False, action='store_true', help="Use CUDA to process on the GPU", dest="cuda")
parser.add_argument('--dtype', default='uint8', choices=['uint8', 'uint16', 'float'], help="Image dtype (uint8, uint16, or float)")
parser.add_argument('--frames', default=3, type=int, help="Number of image frames to generate (default=3)")
parser.add_argument('--image-mode', default='mono', choices=['mono', 'rgb'], help="Image data mode (mono or rgb)", dest='image_mode')
parser.add_argument('--levels', default=None, type=lambda s: tuple([float(x) for x in s.split(',')]), help="min,max levels to scale monochromatic image dynamic range, or rmin,rmax,gmin,gmax,bmin,bmax to scale rgb")
parser.add_argument('--lut', default=False, action='store_true', help="Use color lookup table")
parser.add_argument('--lut-alpha', default=False, action='store_true', help="Use alpha color lookup table", dest='lut_alpha')
parser.add_argument('--size', default='512x512', type=lambda s: tuple([int(x) for x in s.split('x')]), help="WxH image dimensions default='512x512'")
args = parser.parse_args(sys.argv[1:])

if args.cuda and _has_cupy:
    xp = cp
else:
    xp = np

if RawImageGLWidget is not None:
    # don't limit frame rate to vsync
    sfmt = QtGui.QSurfaceFormat()
    sfmt.setSwapInterval(0)
    QtGui.QSurfaceFormat.setDefaultFormat(sfmt)

pg.mkQApp("Video Speed Test Example")

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        ui = ui_template.Ui_MainWindow()
        ui.setupUi(self)
        self.show()

        if RawImageGLWidget is None:
            ui.rawGLRadio.setEnabled(False)
            ui.rawGLRadio.setText(ui.rawGLRadio.text() + " (OpenGL not available)")
        else:
            ui.rawGLImg = RawImageGLWidget()
            ui.stack.addWidget(ui.rawGLImg)

        # read in CLI args
        ui.cudaCheck.setChecked(args.cuda and _has_cupy)
        ui.cudaCheck.setEnabled(_has_cupy)
        ui.framesSpin.setValue(args.frames)
        ui.widthSpin.setValue(args.size[0])
        ui.heightSpin.setValue(args.size[1])
        ui.dtypeCombo.setCurrentText(args.dtype)
        ui.rgbCheck.setChecked(args.image_mode=='rgb')
        ui.maxSpin1.setOpts(value=255, step=1)
        ui.minSpin1.setOpts(value=0, step=1)
        self.levelSpins = [ui.minSpin1, ui.maxSpin1, ui.minSpin2, ui.maxSpin2, ui.minSpin3, ui.maxSpin3]
        if args.levels is None:
            ui.scaleCheck.setChecked(False)
            ui.rgbLevelsCheck.setChecked(False)
        else:
            ui.scaleCheck.setChecked(True)
            if len(args.levels) == 2:
                ui.rgbLevelsCheck.setChecked(False)
                ui.minSpin1.setValue(args.levels[0])
                ui.maxSpin1.setValue(args.levels[1])
            elif len(args.levels) == 6:
                ui.rgbLevelsCheck.setChecked(True)
                for spin,val in zip(self.levelSpins, args.levels):
                    spin.setValue(val)
            else:
                raise ValueError("levels argument must be 2 or 6 comma-separated values (got %r)" % (args.levels,))
        ui.lutCheck.setChecked(args.lut)
        ui.alphaCheck.setChecked(args.lut_alpha)

        #ui.graphicsView.useOpenGL()  ## buggy, but you can try it if you need extra speed.

        self.ui = ui
        self.vb = pg.ViewBox()
        ui.graphicsView.setCentralItem(self.vb)
        self.vb.setAspectLocked()
        self.img = pg.ImageItem()
        self.vb.addItem(self.img)

        self.LUT = None
        self.cache = {}
        self.ptr = 0
        self.lastTime = ptime.time()
        self.fps = None
        self.data = None

        self.connect_signals()
        self.updateScale()
        self.mkData()

        self.timer = QtCore.QTimer(parent=self.img)
        self.timer.timeout.connect(self.update)
        self.timer.start()

    def connect_signals(self):
        ui = self.ui
        ui.gradient.sigGradientChanged.connect(self.updateLUT)
        ui.alphaCheck.toggled.connect(self.updateLUT)

        ui.rgbLevelsCheck.toggled.connect(self.updateScale)
        ui.dtypeCombo.currentIndexChanged.connect(self.mkData)
        ui.rgbCheck.toggled.connect(self.mkData)
        ui.widthSpin.editingFinished.connect(self.mkData)
        ui.heightSpin.editingFinished.connect(self.mkData)
        ui.framesSpin.editingFinished.connect(self.mkData)

        ui.widthSpin.valueChanged.connect(self.updateSize)
        ui.heightSpin.valueChanged.connect(self.updateSize)
        ui.framesSpin.valueChanged.connect(self.updateSize)
        ui.cudaCheck.toggled.connect(self.noticeCudaCheck)

    def updateLUT(self):
        dtype = self.ui.dtypeCombo.currentText()
        if dtype == 'uint8':
            n = 256
        else:
            n = 4096
        self.LUT = self.ui.gradient.getLookupTable(n, alpha=self.ui.alphaCheck.isChecked())
        if _has_cupy and xp == cp:
            self.LUT = cp.asarray(self.LUT)

    def updateScale(self):
        checked = self.ui.rgbLevelsCheck.isChecked()
        for s in self.levelSpins[2:]:
            s.setEnabled(checked)

    def mkData(self):
        frames = self.ui.framesSpin.value()
        width = self.ui.widthSpin.value()
        height = self.ui.heightSpin.value()
        cacheKey = (self.ui.dtypeCombo.currentText(), self.ui.rgbCheck.isChecked(), frames, width, height)
        if cacheKey not in self.cache:
            if cacheKey[0] == 'uint8':
                dt = xp.uint8
                loc = 128
                scale = 64
                mx = 255
            elif cacheKey[0] == 'uint16':
                dt = xp.uint16
                loc = 4096
                scale = 1024
                mx = 2**16 - 1
            elif cacheKey[0] == 'float':
                dt = xp.float32
                loc = 1.0
                scale = 0.1
                mx = 1.0
            else:
                raise ValueError(f"unable to handle dtype: {cacheKey[0]}")
            
            if self.ui.rgbCheck.isChecked():
                shape = (height,width,3)
            else:
                shape = (height,width)
            data = xp.empty((frames,) + shape, dtype=dt)
            for idx in range(frames):
                frame = xp.random.normal(loc=loc, scale=scale, size=shape)
                if cacheKey[0] != 'float':
                    xp.clip(frame, 0, mx, out=frame)
                data[idx] = frame
            data[:, 10:50, 10] = mx
            data[:, 48, 9:12] = mx
            data[:, 47, 8:13] = mx
            self.cache = {cacheKey: data} # clear to save memory (but keep one to prevent unnecessary regeneration)

        self.data = self.cache[cacheKey]
        self.updateLUT()
        self.updateSize()

    def updateSize(self):
        frames = self.ui.framesSpin.value()
        width = self.ui.widthSpin.value()
        height = self.ui.heightSpin.value()
        dtype = xp.dtype(str(self.ui.dtypeCombo.currentText()))
        rgb = 3 if self.ui.rgbCheck.isChecked() else 1
        self.ui.sizeLabel.setText('%d MB' % (frames * width * height * rgb * dtype.itemsize / 1e6))
        self.vb.setRange(QtCore.QRectF(0, 0, width, height))

    def noticeCudaCheck(self):
        global xp
        self.cache = {}
        if self.ui.cudaCheck.isChecked():
            if _has_cupy:
                xp = cp
            else:
                xp = np
                self.ui.cudaCheck.setChecked(False)
        else:
            xp = np
        self.mkData()

    def update(self):
        ui = self.ui
        ptr = self.ptr
        data = self.data

        if ui.lutCheck.isChecked():
            useLut = self.LUT
        else:
            useLut = None

        downsample = ui.downsampleCheck.isChecked()

        if ui.scaleCheck.isChecked():
            if ui.rgbLevelsCheck.isChecked():
                useScale = [
                    [ui.minSpin1.value(), ui.maxSpin1.value()],
                    [ui.minSpin2.value(), ui.maxSpin2.value()],
                    [ui.minSpin3.value(), ui.maxSpin3.value()]]
            else:
                useScale = [ui.minSpin1.value(), ui.maxSpin1.value()]
        else:
            useScale = None

        if ui.rawRadio.isChecked():
            ui.rawImg.setImage(data[ptr%data.shape[0]], lut=useLut, levels=useScale)
            ui.stack.setCurrentIndex(1)
        elif ui.rawGLRadio.isChecked():
            ui.rawGLImg.setImage(data[ptr%data.shape[0]], lut=useLut, levels=useScale)
            ui.stack.setCurrentIndex(2)
        else:
            self.img.setImage(data[ptr%data.shape[0]], autoLevels=False, levels=useScale, lut=useLut, autoDownsample=downsample)
            ui.stack.setCurrentIndex(0)
            #img.setImage(data[ptr%data.shape[0]], autoRange=False)

        self.ptr += 1
        now = ptime.time()
        dt = now - self.lastTime
        self.lastTime = now
        if self.fps is None:
            self.fps = 1.0/dt
        else:
            s = np.clip(dt*3., 0, 1)
            self.fps = self.fps * (1-s) + (1.0/dt) * s
        ui.fpsLabel.setText('%0.2f fps' % self.fps)
        QtCore.QCoreApplication.processEvents()  ## force complete redraw for every plot


mainwin = MainWindow()

if __name__ == '__main__':
    QtWidgets.QApplication.instance().exec_()
