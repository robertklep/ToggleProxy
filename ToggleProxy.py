#!/usr/bin/env python

from    Foundation          import *
from    AppKit              import *
from    SystemConfiguration import *
import  commands, re

class ToggleProxy(NSObject):

    def applicationDidFinishLaunching_(self, notification):
        # find image files
        self.active_image   = NSImage.imageNamed_("active")
        self.inactive_image = NSImage.imageNamed_("inactive")

        # make status bar item
        self.statusitem = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        self.statusitem.retain()
#        self.statusitem.setTarget_(self)
        self.statusitem.setHighlightMode_(False)
        self.statusitem.setEnabled_(True)
        self.statusitem.setImage_(self.inactive_image)

        # insert a menu into the status bar item
        self.menu = NSMenu.alloc().init()
        self.statusitem.setMenu_(self.menu)

        # add items to menu
        self.httpMenuItem = self.menu.addItemWithTitle_action_keyEquivalent_(
            "HTTP proxy",
            "toggleHttpProxy:",
            "")
        self.httpsMenuItem = self.menu.addItemWithTitle_action_keyEquivalent_(
            "HTTPS proxy",
            "toggleHttpsProxy:",
            "")
        self.socksMenuItem = self.menu.addItemWithTitle_action_keyEquivalent_(
            "SOCKS proxy",
            "toggleSocksProxy:",
            "")
        self.menu.addItem_(NSMenuItem.separatorItem())
        self.menu.addItemWithTitle_action_keyEquivalent_(
            "Quit",
            "quitApp:",
            "")

        # open connection to the dynamic (configuration) store
        self.store = SCDynamicStoreCreate(None, "name.klep.toggleproxy", self.dynamicStoreCallback, None)

        # start working
        self.loadNetworkServices()
        self.watchForProxyChanges()
        self.updateProxyStatus()

    @property
    def interface(self):
        # get primary interface
        return SCDynamicStoreCopyValue(self.store, 'State:/Network/Global/IPv4')['PrimaryInterface']

    def loadNetworkServices(self):
        """ load list of network services """
        self.services   = {}
        output          = commands.getoutput("/usr/sbin/networksetup listnetworkserviceorder")
        for servicename, service, device in re.findall(r'\(\d\)\s*(.*?)(?:\n|\r\n?)\(Hardware Port:\s*(.*?), Device:\s*(.*?)\)', output, re.MULTILINE):
            self.services[device] = servicename

    def watchForProxyChanges(self):
        """ install a watcher for proxy changes """
        SCDynamicStoreSetNotificationKeys(self.store, None, [ 'State:/Network/Global/Proxies' ])

        source  = SCDynamicStoreCreateRunLoopSource(None, self.store, 0)
        loop    = NSRunLoop.currentRunLoop().getCFRunLoop()
        CFRunLoopAddSource(loop, source, kCFRunLoopCommonModes)

    def dynamicStoreCallback(self, store, keys, info):
        """ callback for watcher """
        self.updateProxyStatus()

    def updateProxyStatus(self):
        """ update proxy status """
        # load proxy dictionary
        proxydict       = SCDynamicStoreCopyProxies(None)

        # get status for primary interface
        status          = proxydict['__SCOPED__'][self.interface]

        # update menu items according to their related proxy state
        self.httpMenuItem.setState_(  status.get('HTTPEnable', False)  and NSOnState or NSOffState )
        self.httpsMenuItem.setState_( status.get('HTTPSEnable', False) and NSOnState or NSOffState )
        self.socksMenuItem.setState_( status.get('SOCKSEnable', False) and NSOnState or NSOffState )

    def quitApp_(self, sender):
        NSApp.terminate_(self)

    def toggleHttpProxy_(self, sender):
        self.toggleProxy(self.httpMenuItem, 'webproxy')

    def toggleHttpsProxy_(self, sender):
        self.toggleProxy(self.httpsMenuItem, 'securewebproxy')

    def toggleSocksProxy_(self, sender):
        self.toggleProxy(self.socksMenuItem, 'socksfirewallproxy')

    def toggleProxy(self, item, target):
        """ callback for clicks on menu item """
        servicename = self.services.get(self.interface)
        if not servicename:
            NSLog("interface '%s' not found in services?" % self.interface)
            return
        newstate = item.state() == NSOffState and 'on' or 'off'
        commands.getoutput("/usr/sbin/networksetup -set%sstate '%s' %s" % (
            target,
            servicename,
            newstate
        ))
        self.updateProxyStatus()

if __name__ == '__main__':
    sharedapp   = NSApplication.sharedApplication()
    toggler     = ToggleProxy.alloc().init()
    sharedapp.setDelegate_(toggler)
    sharedapp.run()
