# ToggleProxy

_ToggleProxy_ is a [PyObjC][pyobjc]-based application for Mac OS X to
quickly enable and disable the different types of proxy (HTTP, HTTPS,
SOCKS) for the currently active networking interface.

Clicking the icon (an upward arrow, shown in the Mac OS X menu bar)
presents a menu where the state of each type of proxy can be toggled.

*NB*: this is not a proxy manager, you have to configure proxies from Mac
OS X Network preferences first before this app makes any sense.

## Download

You can download a pre-built version from
[the Releases page](https://github.com/robertklep/ToggleProxy/releases).

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
it's not working. If it warrants an issue report, you're welcome!

## Environment

_ToggleProxy_ will call `launchctl` to set various environment variables to point to the current proxy value:

- `http_proxy/HTTP_PROXY`
- `https_proxy/HTTPS_PROXY`
- `ftp_proxy/FTP_PROXY`

To retrieve the current value, you can call this command (from the commandline, or a shell script):

    launchctl getenv http_proxy

## Authors / Contributors

- @robertklep
- @arnaudruffin
- @mkoistinen

## Author & License

Copyright (C) 2011-2013 by Robert Klep (_robert AT klep DOT name_).

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
