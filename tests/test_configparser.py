from pyqtgraph import configfile
import numpy as np
import tempfile, os

def test_longArrays():
    """
    Test config saving and loading of long arrays.
    """
    arr = np.arange(20)
    with tempfile.NamedTemporaryFile(suffix=".cfg") as f:
        configfile.writeConfigFile({'arr': arr}, f.name)
        config = configfile.readConfigFile(f.name)    
    assert all(config['arr'] == arr)

def test_multipleParameters():
    """
    Test config saving and loading of multiple parameters.
    """
    par1 = [1,2,3]
    par2 = "Test"
    par3 = {'a':3,'b':'c'}

    with tempfile.NamedTemporaryFile(suffix=".cfg") as f:
        configfile.writeConfigFile({'par1':par1, 'par2':par2, 'par3':par3}, f.name)
        config = configfile.readConfigFile(f.name)
    
    assert config['par1'] == par1
    assert config['par2'] == par2
    assert config['par3'] == par3
