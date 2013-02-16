#!/usr/bin/env python

from    Foundation          import *
from    AppKit              import *
from    SystemConfiguration import *
# from    pprint              import pprint
import  commands, re

class ToggleProxy(NSObject):

    proxies = {
        'ftp'  : { 'pref': kSCPropNetProxiesFTPEnable,   'title': 'FTP Proxy',   'action': 'toggleFtpProxy:',   'keyEquivalent': "", 'menuitem': None },
        'http' : { 'pref': kSCPropNetProxiesHTTPEnable,  'title': 'HTTP Proxy',  'action': 'toggleHttpProxy:',  'keyEquivalent': "", 'menuitem': None },
        'https': { 'pref': kSCPropNetProxiesHTTPSEnable, 'title': 'HTTPS Proxy', 'action': 'toggleHttpsProxy:', 'keyEquivalent': "", 'menuitem': None },
        'rtsp':  { 'pref': kSCPropNetProxiesRTSPEnable,  'title': 'RTSP Proxy',  'action': 'toggleRtspProxy:',  'keyEquivalent': "", 'menuitem': None },
        'socks': { 'pref': kSCPropNetProxiesSOCKSEnable, 'title': 'SOCKS Proxy', 'action': 'toggleSocksProxy:', 'keyEquivalent': "", 'menuitem': None },
    }

    def applicationDidFinishLaunching_(self, notification):
        # load icon files
        self.icons = {
            '0-0-0' : NSImage.imageNamed_("icon-0-0-0"),
            '1-0-0' : NSImage.imageNamed_("icon-1-0-0"),
            '0-1-0' : NSImage.imageNamed_("icon-0-1-0"),
            '0-0-1' : NSImage.imageNamed_("icon-0-0-1"),
            '1-1-0' : NSImage.imageNamed_("icon-1-1-0"),
            '1-0-1' : NSImage.imageNamed_("icon-1-0-1"),
            '1-1-1' : NSImage.imageNamed_("icon-1-1-1")
        }

        # make status bar item
        self.statusitem = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        self.statusitem.retain()
        self.statusitem.setHighlightMode_(False)
        self.statusitem.setEnabled_(True)
        self.statusitem.setImage_(self.icons['0-0-0'])

        # insert a menu into the status bar item
        self.menu = NSMenu.alloc().init()
        self.statusitem.setMenu_(self.menu)

        # open connection to the dynamic (configuration) store
        self.store = SCDynamicStoreCreate(None, "name.klep.toggleproxy", self.dynamicStoreCallback, None)

        service = self.service

        proxyRef = SCNetworkServiceCopyProtocol(service, kSCNetworkProtocolTypeProxies)
        prefDict = SCNetworkProtocolGetConfiguration(proxyRef)
        # pprint(prefDict)

        separatorRequired = False

        for proxy in self.proxies.values():
            enabled = CFDictionaryGetValue(prefDict, proxy['pref'])
            if enabled is not None:
                proxy['menuitem'] = self.menu.addItemWithTitle_action_keyEquivalent_(
                    proxy['title'],
                    proxy['action'],
                    proxy['keyEquivalent']
                )
                separatorRequired = True
            else:
                # NSLog("%s does not appear to be configured" % proxy['title'])
                proxy['menuitem'] = None

        # pprint(self.proxies)

        if separatorRequired:
            self.menu.addItem_(NSMenuItem.separatorItem())

        self.menu.addItemWithTitle_action_keyEquivalent_(
            "Quit",
            "quitApp:",
            "")

        # start working
        self.loadNetworkServices()
        self.watchForProxyChanges()
        self.updateProxyStatus()

    @property
    def interface(self):
        # get primary interface
        return SCDynamicStoreCopyValue(self.store, 'State:/Network/Global/IPv4')['PrimaryInterface']

    @property
    def service(self):
        """ Returns the service relating to self.interface """
        prefs = SCPreferencesCreate(kCFAllocatorDefault, 'PRG', None)

        # Fetch the list of services
        for serviceRef in SCNetworkServiceCopyAll(prefs):
            interface = SCNetworkServiceGetInterface(serviceRef)
            bsdname   = SCNetworkInterfaceGetBSDName(interface)
            if self.interface == bsdname:
                return serviceRef
        return None

    def loadNetworkServices(self):
        """ Load and store a list of network services indexed by their BSDName """
        self.services   = {}
        # Create a dummy preference reference
        prefs = SCPreferencesCreate(kCFAllocatorDefault, 'PRG', None)
        # Fetch the list of services
        for service in SCNetworkServiceCopyAll(prefs):
            # This is what we're after, the user-defined service name e.g., "Built-in Ethernet"
            name      = SCNetworkServiceGetName(service)
            # Interface reference
            interface = SCNetworkServiceGetInterface(service)
            # The BSDName of the interface, E.g., "en1", this will be the index of our list
            bsdname   = SCNetworkInterfaceGetBSDName(interface)
            self.services[bsdname] = name

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
        proxydict = SCDynamicStoreCopyProxies(None)

        # get status for primary interface
        status    = proxydict['__SCOPED__'][self.interface]

        # update menu items according to their related proxy state
        for proxy in self.proxies.values():
            if proxy['menuitem']:
                proxy['menuitem'].setState_( status.get(proxy['pref'], False) and NSOnState or NSOffState)

        # update icon
        self.statusitem.setImage_(
            self.icons['%d-%d-%d' % (
                status.get(self.proxies['http']['pref'],  False) and 1 or 0,
                status.get(self.proxies['https']['pref'], False) and 1 or 0,
                status.get(self.proxies['socks']['pref'], False) and 1 or 0
            )]
        )

    def quitApp_(self, sender):
        NSApp.terminate_(self)

    def toggleFtpProxy_(self, sender):
        self.toggleProxy(self.proxies['ftp']['menuitem'], 'ftpproxy')

    def toggleHttpProxy_(self, sender):
        self.toggleProxy(self.proxies['http']['menuitem'], 'webproxy')

    def toggleHttpsProxy_(self, sender):
        self.toggleProxy(self.proxies['https']['menuitem'], 'securewebproxy')

    def toggleRtspProxy_(self, sender):
        self.toggleProxy(self.proxies['socks']['menuitem'], 'streamingproxy')

    def toggleSocksProxy_(self, sender):
        self.toggleProxy(self.proxies['socks']['menuitem'], 'socksfirewallproxy')

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
