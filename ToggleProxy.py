#!/usr/bin/env python

from    Foundation          import *
from    AppKit              import *
from    SystemConfiguration import *
import  commands, re, time

class ToggleProxy(NSObject):

    def applicationDidFinishLaunching_(self, notification):
        # define some title-related stuff
        self.active_color   = NSColor.colorWithSRGBRed_green_blue_alpha_(0, 0.5, 0, 1)
        self.inactive_color = NSColor.colorWithSRGBRed_green_blue_alpha_(0.6, 0, 0, 1)
        self.title_font     = NSFont.fontWithName_size_('HelveticaNeue-Bold', 12.0)
        
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

        # start working
        self.loadNetworkServices()
        self.watchForProxyChanges()
        self.updateProxyStatus()

    def loadNetworkServices(self):
        """ load list of network services, the easy way """
        self.services   = {}
        output          = commands.getoutput("/usr/sbin/networksetup listnetworkserviceorder")
        for service, device in re.findall(r'Hardware Port:\s*(.*?), Device:\s*(.*?)\)', output):
            self.services[device] = service

    def watchForProxyChanges(self):
        """ install a watcher for proxy changes """
        store   = SCDynamicStoreCreate(None, "name.klep.toggleproxy", self.proxyStateChanged, None)
        SCDynamicStoreSetNotificationKeys(store, None, [ 'State:/Network/Global/Proxies' ])

        source  = SCDynamicStoreCreateRunLoopSource(None, store, 0)
        loop    = NSRunLoop.currentRunLoop().getCFRunLoop()
        CFRunLoopAddSource(loop, source, kCFRunLoopCommonModes)

    def proxyStateChanged(self, store, keys, info):
        """ callback for watcher """
        self.updateProxyStatus()

    def updateProxyStatus(self):
        """ update proxy status """
        proxydict   = SCDynamicStoreCopyProxies(None)
        interface   = proxydict['__SCOPED__'].keys()[0]
        status      = proxydict['__SCOPED__'][interface]
        self.active = status.get('HTTPEnable', False) and True or False
        self.device = interface

        # set image 
        self.statusitem.setImage_( self.active and self.active_image or self.inactive_image )

        # set tooltip
        if self.active:
            tooltip = "Proxy active on %s:%s" % (
                proxydict.get('HTTPProxy',  '??'),
                proxydict.get('HTTPPort',   '??')
            )
        else:
            tooltip = "Proxy is not active"
        self.statusitem.setToolTip_(tooltip)

    def toggleProxy_(self, sender):
        """ callback for clicks on menu item """
        event = NSApp.currentEvent()

        # Ctrl pressed? if so, quit
        if event.modifierFlags() & NSControlKeyMask:
            NSApp.terminate_(self)
            return

        servicename = self.services.get(self.device)
        if not servicename:
            NSLog("device '%s' not found in services?" % self.device)
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
