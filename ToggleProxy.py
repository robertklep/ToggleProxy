#!/usr/bin/env python

from    Foundation          import *
from    AppKit              import *
from    SystemConfiguration import *
import  commands, re, time

class ToggleProxy(NSObject):

    def applicationDidFinishLaunching_(self, notification):
        # make status bar item
        self.statusitem = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        self.statusitem.retain()
        self.statusitem.setAction_("toggleProxy:")
        self.statusitem.setTarget_(self)
        self.statusitem.setHighlightMode_(False)
        self.statusitem.setEnabled_(True)

        # define some title-related stuff
        self.active_color   = NSColor.colorWithSRGBRed_green_blue_alpha_(0, 0.5, 0, 1)
        self.inactive_color = NSColor.colorWithSRGBRed_green_blue_alpha_(0.6, 0, 0, 1)
        self.title_font     = NSFont.fontWithName_size_('HelveticaNeue-Bold', 12.0)

        # start working
        self.loadNetworkServices()
        self.watchForProxyChanges()
        self.updateProxyStatus()

    def loadNetworkServices(self):
        self.services   = {}
        output          = commands.getoutput("/usr/sbin/networksetup listnetworkserviceorder")
        for service, device in re.findall(r'Hardware Port:\s*(.*?), Device:\s*(.*?)\)', output):
            self.services[device] = service

    def watchForProxyChanges(self):
        store   = SCDynamicStoreCreate(None, "name.klep.toggleproxy", self.proxyStateChanged, None)
        SCDynamicStoreSetNotificationKeys(store, None, [ 'State:/Network/Global/Proxies' ])

        source  = SCDynamicStoreCreateRunLoopSource(None, store, 0)
        loop    = NSRunLoop.currentRunLoop().getCFRunLoop()
        CFRunLoopAddSource(loop, source, kCFRunLoopCommonModes)

    def proxyStateChanged(self, store, keys, info):
        self.updateProxyStatus()

    def updateProxyStatus(self):
        proxydict   = SCDynamicStoreCopyProxies(None)
        interface   = proxydict['__SCOPED__'].keys()[0]
        status      = proxydict['__SCOPED__'][interface]
        self.active = status.get('HTTPEnable', False) and True or False
        self.device = interface

        title       = NSAttributedString.alloc().initWithString_attributes_(
            "Proxy %sactive" % (not self.active and "in" or ""), {
        #        NSFontAttributeName             : self.title_font,
                NSForegroundColorAttributeName  : self.active and self.active_color or self.inactive_color,
            }
        )
        self.statusitem.setAttributedTitle_(title)
        if self.active:
            tooltip = "Proxy active on %s:%s" % (
                proxydict.get('HTTPProxy',  '??'),
                proxydict.get('HTTPPort',   '??')
            )
        else:
            tooltip = ""
        self.statusitem.setToolTip_(tooltip)

    def toggleProxy_(self, sender):
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
