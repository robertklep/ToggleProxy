#!/usr/bin/env python

from    Foundation          import NSLog, kCFRunLoopCommonModes, kCFAllocatorDefault, CFDictionaryGetValue, CFRunLoopAddSource
from    AppKit              import NSObject, NSImage, NSStatusBar, NSVariableStatusItemLength, NSMenu, NSMenuItem, NSRunLoop, NSOnState, NSApp, NSLog, NSOffState, NSApplication
from    SystemConfiguration import kSCNetworkProtocolTypeProxies, kSCPropNetProxiesFTPEnable, kSCPropNetProxiesHTTPEnable, kSCPropNetProxiesHTTPSEnable, kSCPropNetProxiesRTSPEnable, kSCPropNetProxiesSOCKSEnable, kSCNetworkProtocolTypeProxies
from    SystemConfiguration import SCDynamicStoreCreate, SCNetworkServiceCopyProtocol, SCNetworkProtocolGetConfiguration, SCDynamicStoreCopyValue, SCPreferencesCreate, SCNetworkServiceCopyAll, SCNetworkServiceGetInterface, SCNetworkInterfaceGetBSDName, SCDynamicStoreSetNotificationKeys, SCDynamicStoreCreateRunLoopSource, SCDynamicStoreCopyProxies, SCNetworkServiceGetName
import  commands, re

class ToggleProxy(NSObject):

    # This is a dictionary of the proxy-types we support, each with a
    # dictionary of some unique attributes for each, namely:
    #
    #   'pref'          : This is a constant defining which preference itemmarks if this proxy is enabled
    #   'title'         : This is what will appear in the menu
    #   'action'        : This is the method that will be called if the user toggles this proxies menuitem
    #   'keyEquivalent' : Self-explanatory, but unused
    #   'menuitem'      : This will store the menu item for this proxy once it is created

    proxies = {
        'ftp'  : { 'pref': kSCPropNetProxiesFTPEnable,   'title': 'FTP Proxy',   'action': 'toggleFtpProxy:',   'keyEquivalent': "", 'menuitem': None },
        'http' : { 'pref': kSCPropNetProxiesHTTPEnable,  'title': 'HTTP Proxy',  'action': 'toggleHttpProxy:',  'keyEquivalent': "", 'menuitem': None },
        'https': { 'pref': kSCPropNetProxiesHTTPSEnable, 'title': 'HTTPS Proxy', 'action': 'toggleHttpsProxy:', 'keyEquivalent': "", 'menuitem': None },
        'rtsp' : { 'pref': kSCPropNetProxiesRTSPEnable,  'title': 'RTSP Proxy',  'action': 'toggleRtspProxy:',  'keyEquivalent': "", 'menuitem': None },
        'socks': { 'pref': kSCPropNetProxiesSOCKSEnable, 'title': 'SOCKS Proxy', 'action': 'toggleSocksProxy:', 'keyEquivalent': "", 'menuitem': None },
    }

    def applicationDidFinishLaunching_(self, notification):
        # load icon files
        self.active_image   = NSImage.imageNamed_("active")
        self.inactive_image = NSImage.imageNamed_("inactive")

        # make status bar item
        self.statusitem = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        self.statusitem.retain()
        self.statusitem.setHighlightMode_(False)
        self.statusitem.setEnabled_(True)

        # insert a menu into the status bar item
        self.menu = NSMenu.alloc().init()
        self.statusitem.setMenu_(self.menu)

        # open connection to the dynamic (configuration) store
        self.store = SCDynamicStoreCreate(None, "name.klep.toggleproxy", self.dynamicStoreCallback, None)

        proxyRef = SCNetworkServiceCopyProtocol(self.service, kSCNetworkProtocolTypeProxies)
        prefDict = SCNetworkProtocolGetConfiguration(proxyRef)

        separatorRequired = False

        # For each of the proxies we are concerned with, check to see if any
        # are configured. If so (even if not enabled), create a menuitem for
        # that proxy type.

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
                proxy['menuitem'] = None

        if separatorRequired:
            self.menu.addItem_(NSMenuItem.separatorItem())

        # Need a way to quit
        self.menu.addItemWithTitle_action_keyEquivalent_("Quit", "quitApp:", "")

        # Start working
        # self.loadNetworkServices()
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
            if self.interface == SCNetworkInterfaceGetBSDName(interface):
                return serviceRef
        return None

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

        # Are any proxies active now?
        anyProxyEnabled = False

        # update menu items according to their related proxy state
        for proxy in self.proxies.values():
            if proxy['menuitem']:
                proxy['menuitem'].setState_(status.get(proxy['pref'], False) and NSOnState or NSOffState)
                if status.get(proxy['pref'], False):
                    anyProxyEnabled = True

        # set image
        self.statusitem.setImage_(anyProxyEnabled and self.active_image or self.inactive_image)

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
        servicename = SCNetworkServiceGetName(self.service)
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
