#!/usr/bin/env python3
from OSC import OSCServer
import sys
from time import sleep

server = OSCServer( ("localhost", 7110) )
server.timeout = 0
run = True

def user_callback(path, tags, args, source):
    # which user will be determined by path:
    # we just throw away all slashes and join together what's left
    user = ''.join(path.split("/"))
    # tags will contain 'fff'
    # args is a OSCMessage with data
    # source is where the message came from (in case you need to reply)
    print ("Now do something with", user,args[2],args[0],1-args[1]) 

def quit_callback(path, tags, args, source):
    # don't do this at home (or it'll quit blender)
    global run
    run = False

server.addMsgHandler( "/user/1", user_callback )
server.addMsgHandler( "/user/2", user_callback )
server.addMsgHandler( "/user/3", user_callback )
server.addMsgHandler( "/user/4", user_callback )
server.addMsgHandler( "/quit", quit_callback )


def each_frame():
    server.handle_request()

# simulate a "game engine"
while run:
    sleep(1)
    each_frame()

server.close()
