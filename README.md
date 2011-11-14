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

## Prerequisites

* PyObjC: this should be already installed on your Mac, possible after
	installing [XCode][xcode] first;
* [py2app][py2app]

[xcode]: http://itunes.apple.com/us/app/xcode/id448457090?mt=12
[py2app]: https://bitbucket.org/ronaldoussoren/py2app

## Build

Build the application from Terminal like so:

	python setup.py py2app

This builds the application as `dist/ToggleProxy.app`. You can run it from
there, or move it to somewhere more appropriate first.

[pyobjc]: http://pyobjc.sourceforge.net/

## Troubleshooting

If you run into problems, first try to find out what the reason is. Run
this from the same directory as `setup.py`:

	./dist/ToggleProxy.app/Contents/MacOS/ToggleProxy

This should output any errors to stdout, so you might get a clue as to why
it's not working. If it warrants an issue-report, you're welcome!

## Author & License

Copyright (C) 2011 by Robert Klep (_robert AT klep DOT name_).

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or
    sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:
    
    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
