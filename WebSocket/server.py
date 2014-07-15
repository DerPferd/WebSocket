###############################################################################
##
##  Copyright (C) 2013-2014 Jonathan Beaulieu <123.jonathan@gmail.com>
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU Affero General Public License as published
##  by the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##  You may obtain a copy of the License at
##
##      http://www.gnu.org/licenses/agpl
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU Affero General Public License for more details.
##
###############################################################################

from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol
from twisted.internet import reactor
import json
try:
	from encoder import Encoder
	from encoder import decoder
	print("Loaded Encoder")
	using_encoder = True
except ImportError:
	print("Failed to load Encoder!")
	using_encoder = False

class Server:
	def __init__(self, hostname="localhost", port="9876", msgHandlers={}):
		self.hostname = hostname
		self.port = port
		self.factory = WebSocketServerFactory("ws://" + hostname + ":" + port, debug=False)
		ServerProtocol.msgHandlers = msgHandlers
		self.factory.protocol = ServerProtocol
		reactor.listenTCP(int(self.port), self.factory)

	def run(self):
		print "Running on port: " + self.port
		reactor.run()


class ServerProtocol(WebSocketServerProtocol):
	def onConnection(self, request):
		print("Client connecting: {0}".format(request.peer))

	def onOpen(self):
		print("WebSocket connection open.")
		if "onOpen" in self.msgHandlers:
			self.msgHandlers["onOpen"]()

	def onMessage(self, msg, binary):
		print "Got message: " + str(msg)
		try:
			if using_encoder:
				msg = json.loads(msg, object_hook=decoder)
			else:
				msg = json.loads(msg)
		except:
			print "Warning: Could not load json."
			self.send({"header": "warning", "description": "Could not load json."})
			return False
		print msg
		if msg:
			if "_cmd" in msg:
				if msg["_cmd"] in self.msgHandlers:
					self.msgHandlers[msg["_cmd"]](msg, self)
				else:   
					print "Warning: No matching command."
					self.send({"header": "warning", "description": "No matching command.", "_cmd": msg["_cmd"]})
			else:   
				print "Warning: No command in message."
				self.send({"header": "warning", "description": "No command in message."})
		else:   
			print "Warning: Empty message."
			self.send({"header": "warning", "description": "Empty message."})
			return False

	def send(self, msg):
		print("Sending... ", msg)
		try:
			if using_encoder:
				msg = json.dumps(msg, cls=Encoder)
			else:
				msg = json.dumps(msg)
		except:
			print "Error: Could not convert object to json."
			self.sendMessage('{"header": "error", "description": "Server error 301."}')
			raise Exception("Could not convert object to json.")
		print "Sending: " + msg
		self.sendMessage(msg)

	def onClose(self, wasClean, code, reason):
		print("WebSocket connection closed: {0}".format(reason))
		if "onClose" in self.msgHandlers:
			self.msgHandlers["onClose"](self, {"wasClean": wasClean, "code": code, "reason": reason})