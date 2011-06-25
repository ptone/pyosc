#!/usr/bin/env python3
from OSC import OSCClient, OSCMessage

client = OSCClient()
client.connect( ("localhost", 7110) )

user = OSCMessage("/user/1")
user.append( [1.0, 2.0, 3.0 ] )
client.send(user)

user = OSCMessage("/user/2")
user.append( [2.0, 3.0, 4.0 ] )
client.send(user)

user = OSCMessage("/user/3")
user.append( [2.0, 3.0, 3.1 ] )
client.send(user)

user = OSCMessage("/user/4")
user.append( [3.2, 3.4, 6.0 ] )
client.send(user)


client.send( OSCMessage("/quit") )

