from    distutils.core  import setup
from    glob            import glob
import  py2app, sys, os, commands

# define distutils setup structure
setup(
    app         = [ 'ProxySwitcher.py' ],
    options     = dict(py2app = dict(
        plist   = dict(
            LSBackgroundOnly = True
        )
    ))
)
