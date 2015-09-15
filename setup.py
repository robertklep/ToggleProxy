from    distutils.core  import setup
from    glob            import glob
import  py2app, sys, os, commands

# determine version by latest tag
status, version = commands.getstatusoutput("git describe --abbrev=0 --tags")
if status != 0:
    # probably no hg installed or not building from a repository
    version = "unknown"
if version[0] == 'v':
    version = version[1:]

setup(
    app         = [ 'ToggleProxy.py' ],
    version     = version,
    data_files  = glob('resources/*.png'),
    options     = dict(py2app = dict(
        plist   = dict(
            CFBundleIdentifier = 'name.klep.toggleproxy',
            LSBackgroundOnly   = True,
        )
    ))
)
