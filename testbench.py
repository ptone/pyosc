#!/usr/bin/env python

from OSC import *
from OSC import _readString, _readFloat, _readInt

if __name__ == "__main__":
	import optparse
	
	default_port = 2222
		
	# define command-line options
	op = optparse.OptionParser(description="OSC.py OpenSoundControl-for-Python Test Program")
	op.add_option("-l", "--listen", dest="listen",
			help="listen on given host[:port]. default = '0.0.0.0:%d'" % default_port)
	op.add_option("-s", "--sendto", dest="sendto",
			help="send to given host[:port]. default = '127.0.0.1:%d'" % default_port)
	op.add_option("-t", "--threading", action="store_true", dest="threading",
			help="Test ThreadingOSCServer")
	op.add_option("-f", "--forking", action="store_true", dest="forking",
			help="Test ForkingOSCServer")
	op.add_option("-u", "--usage", action="help", help="show this help message and exit")
	
	op.set_defaults(listen=":%d" % default_port)
	op.set_defaults(sendto="")
	op.set_defaults(threading=False)
	op.set_defaults(forking=False)

	# Parse args
	(opts, args) = op.parse_args()
	
	addr, server_prefix = parseUrlStr(opts.listen)
	if addr != None and addr[0] != None:
		if addr[1] != None:
			listen_address = addr
		else:
			listen_address = (addr[0], default_port)
	else:
		listen_address = ('', default_port)
			
	targets = {}
	for trg in opts.sendto.split(','):
		(addr, prefix) = parseUrlStr(trg)
		if len(prefix):	
			(prefix, filters) = parseFilterStr(prefix)
		else:
			filters = {}
		
		if addr != None:
			if addr[1] != None:
				targets[addr] = [prefix, filters]
			else:
				targets[(addr[0], listen_address[1])] = [prefix, filters]
		elif len(prefix) or len(filters):
			targets[listen_address] = [prefix, filters]
			
	welcome = "Welcome to the OSC testing program."
	print welcome
	hexDump(welcome)
	print
	message = OSCMessage()
	message.setAddress("/print")
	message.append(44)
	message.append(11)
	message.append(4.5)
	message.append("the white cliffs of dover")
	
	print message
	hexDump(message.getBinary())

	print "\nMaking and unmaking a message.."

	strings = OSCMessage("/prin{ce,t}")
	strings.append("Mary had a little lamb")
	strings.append("its fleece was white as snow")
	strings.append("and everywhere that Mary went,")
	strings.append("the lamb was sure to go.")
	strings.append(14.5)
	strings.append(14.5)
	strings.append(-400)

	raw  = strings.getBinary()

	print strings
	hexDump(raw)

	print "Retrieving arguments..."
	data = raw
	for i in range(6):
		text, data = _readString(data)
		print text

	number, data = _readFloat(data)
	print number

	number, data = _readFloat(data)
	print number

	number, data = _readInt(data)
	print number

	print decodeOSC(raw)

	print "\nTesting Blob types."

	blob = OSCMessage("/pri*")
	blob.append("","b")
	blob.append("b","b")
	blob.append("bl","b")
	blob.append("blo","b")
	blob.append("blob","b")
	blob.append("blobs","b")
	blob.append(42)

	print blob
	hexDump(blob.getBinary())

	print1 = OSCMessage()
	print1.setAddress("/print")
	print1.append("Hey man, that's cool.")
	print1.append(42)
	print1.append(3.1415926)

	print "\nTesting OSCBundle"

	bundle = OSCBundle()
	bundle.append(print1)
	bundle.append({'addr':"/print", 'args':["bundled messages:", 2]})
	bundle.setAddress("/*print")
	bundle.append(("no,", 3, "actually."))

	print bundle
	hexDump(bundle.getBinary())
	
	# Instantiate OSCClient
	print "\nInstantiating OSCClient:"
	if len(targets):
		c = OSCMultiClient()
		c.updateOSCTargets(targets)
	else:
		c = OSCClient()
		c.connect(listen_address)	# connect back to our OSCServer
	
	print c
	if hasattr(c, 'getOSCTargetStrings'):
		print "Sending to:"
		for (trg, filterstrings) in c.getOSCTargetStrings():
			out = trg
			for fs in filterstrings:
				out += " %s" % fs
				
			print out

	# Now an OSCServer...
	print "\nInstantiating OSCServer:"
	
	# define a message-handler function for the server to call.
	def printing_handler(addr, tags, stuff, source):
		msg_string = "%s [%s] %s" % (addr, tags, str(stuff))
		sys.stdout.write("OSCServer Got: '%s' from %s\n" % (msg_string, getUrlStr(source)))
		
		# send a reply to the client.
		msg = OSCMessage("/printed")
		msg.append(msg_string)
		return msg

	if opts.threading:
		s = ThreadingOSCServer(listen_address, c, return_port=listen_address[1])
	elif opts.forking:
		s = ForkingOSCServer(listen_address, c, return_port=listen_address[1])
	else:
		s = OSCServer(listen_address, c, return_port=listen_address[1])
	
	print s
	
	# Set Server to return errors as OSCMessages to "/error"
	s.setSrvErrorPrefix("/error")
	# Set Server to reply to server-info requests with OSCMessages to "/serverinfo"
	s.setSrvInfoPrefix("/serverinfo")
	
	# this registers a 'default' handler (for unmatched messages), 
	# an /'error' handler, an '/info' handler.
	# And, if the client supports it, a '/subscribe' & '/unsubscribe' handler
	s.addDefaultHandlers()

	s.addMsgHandler("/print", printing_handler)
	
	# if client & server are bound to 'localhost', server replies return to itself!
	s.addMsgHandler("/printed", s.msgPrinter_handler)
	s.addMsgHandler("/serverinfo", s.msgPrinter_handler)
	
	print "Registered Callback-functions:"
	for addr in s.getOSCAddressSpace():
		print addr
		
	print "\nStarting OSCServer. Use ctrl-C to quit."
	st = threading.Thread(target=s.serve_forever)
	st.start()
	
	if hasattr(c, 'targets') and listen_address not in c.targets.keys():
		print "\nSubscribing local Server to local Client"
		c2 = OSCClient()
		c2.connect(listen_address)
		subreq = OSCMessage("/subscribe")
		subreq.append(listen_address)

		print "sending: ", subreq
		c2.send(subreq)
		c2.close()

		time.sleep(0.1)
	
	print "\nRequesting OSC-address-space and subscribed clients from OSCServer"
	inforeq = OSCMessage("/info")
	for cmd in ("info", "list", "clients"):
		inforeq.clearData()
		inforeq.append(cmd)
	
		print "sending: ", inforeq
		c.send(inforeq)
		
		time.sleep(0.1)
	
	print2 = print1.copy()
	print2.setAddress('/noprint')
	
	print "\nSending Messages"
	
	for m in (message, print1, print2, strings, bundle):
		print "sending: ", m
		c.send(m)

		time.sleep(0.1)
		
	print "\nThe next message's address will match both the '/print' and '/printed' handlers..."
	print "sending: ", blob
	c.send(blob)
	
	time.sleep(0.1)

	print "\nBundles can be given a timestamp.\nThe receiving server should 'hold' the bundle until its time has come"
	
	waitbundle = OSCBundle("/print")
	waitbundle.setTimeTag(time.time() + 5)
	if s.__class__ == OSCServer:
		waitbundle.append("Note how the (single-thread) OSCServer blocks while holding this bundle")
	else:
		waitbundle.append("Note how the %s does not block while holding this bundle" % s.__class__.__name__)
	
	print "Set timetag 5 s into the future"
	print "sending: ", waitbundle
	c.send(waitbundle)
	
	time.sleep(0.1)

	print "Recursing bundles, with timetags set to 10 s [25 s, 20 s, 10 s]"
	bb = OSCBundle("/print")
	bb.setTimeTag(time.time() + 10)
	
	b = OSCBundle("/print")
	b.setTimeTag(time.time() + 25)
	b.append("held for 25 sec")
	bb.append(b)
	
	b.clearData()
	b.setTimeTag(time.time() + 20)
	b.append("held for 20 sec")
	bb.append(b)
	
	b.clearData()
	b.setTimeTag(time.time() + 15)
	b.append("held for 15 sec")
	bb.append(b)
	
	if s.__class__ == OSCServer:
		bb.append("Note how the (single-thread) OSCServer handles the bundle's contents in order of appearance")
	else:
		bb.append("Note how the %s handles the sub-bundles in the order dictated by their timestamps" % s.__class__.__name__)
		bb.append("Each bundle's contents, however, are processed in random order (dictated by the kernel's threading)")
	
	print "sending: ", bb
	c.send(bb)
	
	time.sleep(0.1)

	print "\nMessages sent!"
	
	print "\nWaiting for OSCServer. Use ctrl-C to quit.\n"
	
	try:
		while True:
			time.sleep(30)
	
	except KeyboardInterrupt:
		print "\nClosing OSCServer."
		s.close()
		print "Waiting for Server-thread to finish"
		st.join()
		print "Closing OSCClient"
		c.close()
		print "Done"
		
	sys.exit(0)
