#!/usr/bin/env python

from Foundation import NSLog, kCFRunLoopCommonModes, kCFAllocatorDefault, CFDictionaryGetValue, CFRunLoopAddSource,  NSUserDefaults
from AppKit import NSObject, NSImage, NSStatusBar, NSVariableStatusItemLength, NSMenu, NSMenuItem, NSRunLoop, NSOnState, NSApp, NSLog, NSOffState, NSApplication
from SystemConfiguration import kSCNetworkProtocolTypeProxies, kSCPropNetProxiesFTPEnable, kSCPropNetProxiesHTTPEnable, kSCPropNetProxiesHTTPSEnable, kSCPropNetProxiesRTSPEnable, kSCPropNetProxiesSOCKSEnable, kSCPropNetProxiesFTPProxy, kSCPropNetProxiesHTTPProxy, kSCPropNetProxiesHTTPSProxy, kSCPropNetProxiesRTSPProxy, kSCPropNetProxiesSOCKSProxy, kSCPropNetProxiesFTPPort, \
    kSCPropNetProxiesHTTPPort, kSCPropNetProxiesHTTPSPort, kSCPropNetProxiesRTSPPort, kSCPropNetProxiesSOCKSPort, kSCNetworkProtocolTypeProxies
from SystemConfiguration import SCDynamicStoreCreate, SCNetworkServiceCopyProtocol, SCNetworkProtocolGetConfiguration, SCDynamicStoreCopyValue, SCPreferencesCreate, SCNetworkServiceCopyAll, SCNetworkServiceGetInterface, SCNetworkInterfaceGetBSDName, SCDynamicStoreSetNotificationKeys, SCDynamicStoreCreateRunLoopSource, SCDynamicStoreCopyProxies, SCNetworkServiceGetName
import commands, re

class ToggleProxy(NSObject):
    # This is a dictionary of the proxy-types we support, each with a
    # dictionary of some unique attributes for each, namely:
    #
    # 'prefEnable'    : This is a constant defining which preference item marks if this proxy is enabled
    # 'prefProxy'     : This is a constant defining which preference item holds the proxy host
    # 'prefPort'      : This is a constant defining which preference item holds the proxy port
    # 'title'         : This is what will appear in the menu
    # 'action'        : This is the method that will be called if the user toggles this proxies menuitem
    # 'keyEquivalent' : Self-explanatory
    # 'menuitem'      : This will store the menu item for this proxy once it is created
    # 'envVariable'   : Environment variable to set with system proxy settings, if needed

    proxyTypes = {
        'http': {'prefEnable': kSCPropNetProxiesHTTPEnable,
                 'prefProxy': kSCPropNetProxiesHTTPProxy,
                 'prefPort': kSCPropNetProxiesHTTPPort,
                 'title': 'HTTP Proxy',
                 'action': 'toggleHttpProxy:',
                 'keyEquivalent': "",
                 'menuitem': None,
                 'envVariable': {"http_proxy", "HTTP_PROXY"}},
        'https': {'prefEnable': kSCPropNetProxiesHTTPSEnable,
                  'prefProxy': kSCPropNetProxiesHTTPSProxy,
                  'prefPort': kSCPropNetProxiesHTTPSPort,
                  'title': 'HTTPS Proxy', 'action': 'toggleHttpsProxy:',
                  'keyEquivalent': "",
                  'menuitem': None,
                  'envVariable': {"https_proxy", "HTTPS_PROXY"}},
        'ftp': {'prefEnable': kSCPropNetProxiesFTPEnable,
                'prefProxy': kSCPropNetProxiesFTPProxy,
                'prefPort': kSCPropNetProxiesFTPPort,
                'title': 'FTP Proxy',
                'action': 'toggleFtpProxy:',
                'keyEquivalent': "",
                'menuitem': None,
                'envVariable': {"ftp_proxy", "FTP_PROXY"}},
        'rtsp': {'prefEnable': kSCPropNetProxiesRTSPEnable,
                 'prefProxy': kSCPropNetProxiesRTSPProxy,
                 'prefPort': kSCPropNetProxiesRTSPPort,
                 'title': 'RTSP Proxy',
                 'action': 'toggleRtspProxy:',
                 'keyEquivalent': "",
                 'menuitem': None,
                 'envVariable': None},
        'socks': {'prefEnable': kSCPropNetProxiesSOCKSEnable,
                  'prefProxy': kSCPropNetProxiesSOCKSProxy,
                  'prefPort': kSCPropNetProxiesSOCKSPort,
                  'title': 'SOCKS Proxy',
                  'action': 'toggleSocksProxy:',
                  'keyEquivalent': "",
                  'menuitem': None,
                  'envVariable': None},
    }

    def log(self, content):
        # Toggle logging from Terminal:
        # $ defaults write name.klep.toggleproxy logging -bool YES/NO
        if NSUserDefaults.standardUserDefaults().boolForKey_("logging"):
            NSLog(content)

    def applicationDidFinishLaunching_(self, notification):
        # load icon files
        self.active_image     = NSImage.imageNamed_("StatusBarImage")
        self.inactive_image   = NSImage.imageNamed_("StatusBarImage-inactive")
        self.no_network_image = NSImage.imageNamed_("StatusBarImage-noNetwork")
        self.active_image.setTemplate_(True)
        self.inactive_image.setTemplate_(True)
        self.no_network_image.setTemplate_(True)

        # make status bar item
        self.statusitem = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        self.statusitem.retain()
        self.statusitem.setHighlightMode_(False)
        self.statusitem.setEnabled_(True)

        # insert a menu into the status bar item
        self.menu = NSMenu.alloc().init()
        self.statusitem.setMenu_(self.menu)

        # open connection to the dynamic (configuration) store
        self.store    = SCDynamicStoreCreate(None, "name.klep.toggleproxy", self.dynamicStoreCallback, None)
        self.prefDict = SCNetworkProtocolGetConfiguration(SCNetworkServiceCopyProtocol(self.service, kSCNetworkProtocolTypeProxies))
        self.constructMenu()

        self.watchForProxyOrIpChanges()
        self.updateUI()
        self.setEnvVariables()

    @property
    def is_ip_assigned(self):
        return SCDynamicStoreCopyValue(self.store, 'State:/Network/Global/IPv4') is not None

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

    def constructMenu(self):
        self.menu.removeAllItems()

        separator_required = False
        if self.is_ip_assigned:
            # For each of the proxyTypes we are concerned with, check to see if any
            # are configured. If so (even if not enabled), create a menuitem for
            # that proxy type.
            for proxy in self.proxyTypes.values():
                enabled = CFDictionaryGetValue(self.prefDict, proxy['prefEnable'])
                if enabled is not None:
                    proxy['menuitem'] = self.menu.addItemWithTitle_action_keyEquivalent_(
                        proxy['title'],
                        proxy['action'],
                        proxy['keyEquivalent']
                    )
                    separator_required = True
                else:
                    proxy['menuitem'] = None
        else:
            self.menu.addItemWithTitle_action_keyEquivalent_("No connection - Please connect to any network before using this tool", None, "")

        if separator_required:
            self.menu.addItem_(NSMenuItem.separatorItem())

         # Need a way to quit
        self.menu.addItemWithTitle_action_keyEquivalent_("Quit", "quitApp:", "q")


    def watchForProxyOrIpChanges(self):
        """ install a watcher for proxy and Ip changes """
        SCDynamicStoreSetNotificationKeys(self.store, None, ['State:/Network/Global/Proxies', 'State:/Network/Global/IPv4'])
        source = SCDynamicStoreCreateRunLoopSource(None, self.store, 0)
        loop   = NSRunLoop.currentRunLoop().getCFRunLoop()
        CFRunLoopAddSource(loop, source, kCFRunLoopCommonModes)

    def dynamicStoreCallback(self, store, keys, info):
        """ callback for watcher """
        self.log("Proxy or IP change detected")

        # could be an interface change, we have to rebuild menu from scratch in case the proxy configuration is different
        self.constructMenu()
        self.updateUI()
        self.setEnvVariables()

    def updateUI(self):
        if self.is_ip_assigned:
            self.log("Update proxy status on menu items")
            # load proxy dictionary
            proxydict = SCDynamicStoreCopyProxies(None)

            # get status for primary interface
            status = proxydict['__SCOPED__'][self.interface]

            # Are any proxies active now?
            anyProxyEnabled = False

            # update menu items according to their related proxy state
            for proxy in self.proxyTypes.values():
                if proxy['menuitem']:
                    proxy['menuitem'].setState_(status.get(proxy['prefEnable'], False) and NSOnState or NSOffState)
                    if status.get(proxy['prefEnable'], False):
                        anyProxyEnabled = True

            # set image
            self.statusitem.setImage_(anyProxyEnabled and self.active_image or self.inactive_image)
        else:
            self.statusitem.setImage_(self.no_network_image)

    def setEnvVariables(self):
        if self.is_ip_assigned:
            self.log("Setting env var according to system settings")
            # load proxy dictionary
            proxydict = SCDynamicStoreCopyProxies(None)
            # get status for primary interface
            status = proxydict['__SCOPED__'][self.interface]
            # update menu items according to their related proxy state
            for proxy in self.proxyTypes.values():
                if proxy['menuitem'] and proxy['envVariable']:
                    if status.get(proxy['prefEnable'], False):
                        for envvar in proxy['envVariable']:
                            self.executeCommand("launchctl setenv %s '%s'" % (envvar, "http://" + CFDictionaryGetValue(self.prefDict, proxy['prefProxy']) + ":" + str(CFDictionaryGetValue(self.prefDict, proxy['prefPort']))))
                    else:
                        for envvar in proxy['envVariable']:
                            self.executeCommand("launchctl unsetenv %s" % envvar)

    def quitApp_(self, sender):
        NSApp.terminate_(self)

    def toggleFtpProxy_(self, sender):
        self.toggleProxy(self.proxyTypes['ftp']['menuitem'], 'ftpproxy')

    def toggleHttpProxy_(self, sender):
        self.toggleProxy(self.proxyTypes['http']['menuitem'], 'webproxy')

    def toggleHttpsProxy_(self, sender):
        self.toggleProxy(self.proxyTypes['https']['menuitem'], 'securewebproxy')

    def toggleRtspProxy_(self, sender):
        self.toggleProxy(self.proxyTypes['rtsp']['menuitem'], 'streamingproxy')

    def toggleSocksProxy_(self, sender):
        self.toggleProxy(self.proxyTypes['socks']['menuitem'], 'socksfirewallproxy')

    def executeCommand(self, command):
        self.log("[Exec Command] %s" % command)
        commands.getoutput(command)

    def toggleProxy(self, item, target):
        """ callback for clicks on menu item """
        servicename = SCNetworkServiceGetName(self.service)
        if not servicename:
            self.log("interface '%s' not found in services?" % self.interface)
            return

        newstate = item.state() == NSOffState and 'on' or 'off'

        # Sometimes the UI will be updated too fast if we don't wait a little
        # (resulting in wrongly enabled proxies in the menu), so after changing
        # the interface state we wait a bit (this is easier than doing a sleep
        # in code, as that has to be scheduled on the run loop)
        self.executeCommand("/usr/sbin/networksetup -set%sstate '%s' %s; sleep 1" % (
            target,
            servicename,
            newstate
        ))
        self.updateUI()
        self.setEnvVariables()

if __name__ == '__main__':
    sharedapp = NSApplication.sharedApplication()
    toggler = ToggleProxy.alloc().init()
    sharedapp.setDelegate_(toggler)
    sharedapp.run()
