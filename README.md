# ToggleProxy

_ToggleProxy_ is a [PyObjC][pyobjc]-based application for Mac OS X to
quickly enable and disable the HTTP proxy for the currently active
networking interface.

It's a _headless_ application which installs a menu item in the Mac OS
X menu bar. The item shows either an up-arrow with a dashed line through it
(think _traffic is going through a proxy_) when the proxy is active, and
only an up-arrow when the proxy is not active.

## Build

To build the application, you'll have the Developer tools for Mac OS
X installed.

When you have, you first build the application:
    python setup.py py2app

This builds the application as `dist/ToggleProxy.app`. You can run it from
there, or move it to somewhere more appropriate first.
