#!/usr/bin/python

import sys
import os
import dbus
import gobject

from multiprocessing import Process
from pyrowl import Pyrowl
from daemon import Daemon
from dbus.mainloop.glib import DBusGMainLoop
from HTMLParser import HTMLParser

# Stripping html tags with only stdlib
# From Eloff @ StackOverflow
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


class Pronto(Daemon):
    
    def setup(self):
                
        self.pyrowl = Pyrowl()
        
        __dir__ = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(__dir__, 'api.key')
        if os.path.isfile(filepath):
            keys = filter(None, open(filepath,'r').read().split("\n"))
            self.pyrowl.addkey(keys)   
        else:
            print "Pronto - Send notifications to your iDevice via Prowl"
            print "Copyright (c) 2011 Luqman Aden"
            print ""
            print "No API key found. Create file name 'api.key' with on API per line."
    
    def pusher(self, application, event, description, url = '', priority = 0, batch = False):
                
        self.pyrowl.push(application, event, description, url, priority, batch)
                
    def run(self):
        
        # Monitor DBUS    
        DBusGMainLoop(set_as_default=True)
        
        bus = dbus.SessionBus()
        
        # We only want notifications, filter the rest out
        bus.add_match_string_non_blocking('interface=org.freedesktop.Notifications,eavesdrop=true')
        
        # Send the notifications/events to our handler
        bus.add_message_filter(self.handler)
        
        loop = gobject.MainLoop()
        loop.run()
                
    def handler(self, *args):
                
        if args[1].get_interface() == "org.freedesktop.Notifications" and args[1].get_member() == "Notify":
    
            method_args = args[1].get_args_list()
            
            if len(method_args[3].strip()):
                
                application = method_args[0]
                event = "%s" % method_args[3]
                description = "%s" % strip_tags(method_args[4])
                priority = 0 # Set to normal by default
                
                if method_args[6].get('urgency', 1) == 0:  
                    priority = -1 # Low
                elif method_args[6].get('urgency', 1) == 1:
                    priority = 0 # normal
                elif method_args[6].get('urgency', 1) == 2:
                    priority = 2 # critical
                
                pusher_process = Process(target=self.pusher, args=(application, event, description, '', priority, False))
                pusher_process.start()
    
if __name__ == "__main__":
    
    pronto = Pronto('/tmp/pronto.pid')
    pronto.setup()
    if len(sys.argv) == 2:
        
        if sys.argv[1] == 'start':
            pronto.start()
        elif sys.argv[1] == 'stop':
            pronto.stop()
        elif sys.argv[1] == 'restart':
            pronto.restart()
        else:
            print "Pronto - Send notifications to your iDevice via Prowl"
            print "Copyright (c) 2011 Luqman Aden"
            print ""
            print "Pronto: Unknown command."
            print "Usage: %s start|stop|restart" % sys.argv[0]
                
            sys.exit(2)
            
        sys.exit(0)
        
    else:
        
        print "Pronto - Send notifications to your iDevice via Prowl"
        print "Copyright (c) 2011 Luqman Aden"
        print "Usage: %s start|stop|restart" % sys.argv[0]
            
        sys.exit(2)
        
