from    distutils.core  import setup
from    glob            import glob
import  py2app, sys, os, commands

setup(
    app         = [ 'ToggleProxy.py' ],
    data_files  = glob('resources/*.png'),
    options     = dict(py2app = dict(
        plist   = dict(
            CFBundleIdentifier = 'name.klep.toggleproxy',
            LSBackgroundOnly   = True,
        )
    ))
)
