# ToggleProxy

_ToggleProxy_ is a [PyObjC][pyobjc]-based application for Mac OS X to
quickly enable and disable the HTTP proxy for the currently active
networking interface.

It's a background application which installs a menu item in the Mac OS
X menu bar. The item shows either an up-arrow with a dashed line through it
(think _traffic is going through a proxy_) when the proxy is active, and
only an up-arrow when the proxy is not active.

Toggle the on/off state by clicking the icon, quit the application by
`Ctrl`-clicking the icon.

## Build

To build the application, you'll have the Developer tools for Mac OS
X installed.

When you have, you first build the application:

	python setup.py py2app

This builds the application as `dist/ToggleProxy.app`. You can run it from
there, or move it to somewhere more appropriate first.

[pyobjc]: http://pyobjc.sourceforge.net/

## Troubleshooting

On Mac OS X Lion, you might get errors running the application. If that
happens, first try to find out what the reason is. Run this from the same
directory as `setup.py`:

	./dist/ToggleProxy.app/Contents/MacOS/ToggleProxy

If you're getting errors about frameworks not being found, you might have
to install a different version of the `py2app` module. I'm using [this
one][py2app].

[py2app]: https://bitbucket.org/ronaldoussoren/py2app
