#!/usr/bin/env python

from    Foundation          import *
from    AppKit              import *
from    SystemConfiguration import *
import  commands, re, time

class ToggleProxy(NSObject):

    def applicationDidFinishLaunching_(self, notification):
        # find image files
        self.active_image   = NSImage.imageNamed_("active")
        self.inactive_image = NSImage.imageNamed_("inactive")

        # make status bar item
        self.statusitem = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        self.statusitem.retain()
        self.statusitem.setAction_("toggleProxy:")
        self.statusitem.setTarget_(self)
        self.statusitem.setHighlightMode_(False)
        self.statusitem.setEnabled_(True)

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
        self.services = {}
        for key, dictionary in SCDynamicStoreCopyMultiple(self.store, None, [ 'Setup:/Network/Service/.*/Interface' ]).items():
            self.services[dictionary['DeviceName']] = dictionary['UserDefinedName']

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
        self.active     = status.get('HTTPEnable', False) and True or False

        # set image
        self.statusitem.setImage_( self.active and self.active_image or self.inactive_image )

        # set tooltip
        if self.active:
            tooltip = "[%s] proxy active on %s:%s" % (
                self.interface,
                proxydict.get('HTTPProxy',  '??'),
                proxydict.get('HTTPPort',   '??'),
            )
        else:
            tooltip = "[%s] proxy not active" % self.interface
        self.statusitem.setToolTip_(tooltip)

    def toggleProxy_(self, sender):
        """ callback for clicks on menu item """
        event = NSApp.currentEvent()

        # Ctrl pressed? if so, quit
        if event.modifierFlags() & NSControlKeyMask:
            NSApp.terminate_(self)
            return

        servicename = self.services.get(self.interface)
        if not servicename:
            NSLog("interface '%s' not found in services?" % self.interface)
            return
        newstate = self.active and "off" or "on"
        commands.getoutput("networksetup setwebproxystate %s %s" % (
            servicename,
            newstate
        ))
        self.updateProxyStatus()

if __name__ == '__main__':
    sharedapp   = NSApplication.sharedApplication()
    toggler     = ToggleProxy.alloc().init()
    sharedapp.setDelegate_(toggler)
    sharedapp.run()
