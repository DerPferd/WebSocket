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
	def __init__(self, protocol, hostname="localhost", port="9876"):
		self.hostname = hostname
		self.port = port
		self.factory = WebSocketServerFactory("ws://" + hostname + ":" + port, debug=False)
		self.factory.protocol = protocol
		reactor.listenTCP(int(self.port), self.factory)

	def run(self):
		print "Running on port: " + self.port
		reactor.run()

class Handler(object):
        """The is a decorator for a handler inside a ServerProtocol class"""
        def __init__(self, requiredArgs=[], optionalArgs=[]):
                self.requiredArgs = requiredArgs
                self.optionalArgs = optionalArgs
        
        def __call__(selfD, f):
                def wrapped_f(self, request):
                        if "params" in request:
                                kwargs = request["params"]
                        else:
                                kwargs = {}
                        # check if missing required args
                        if set(selfD.requiredArgs)-set(kwargs.keys())!=set():
                                self.sendError(request, ServerProtocolV1.INVALID_PARAMS_ERROR)
                                return
                        # check if all args are accounted for
                        elif set(kwargs.keys())-set(selfD.requiredArgs+selfD.optionalArgs)!=set():
                                self.sendError(request, ServerProtocolV1.INVALID_PARAMS_ERROR)
                                return
                        return f(self, request, **kwargs)
                return wrapped_f


class ServerProtocolV1(WebSocketServerProtocol):
        VERSION = "1.0"
        JSON_PARSE_ERROR = {"code": -32700, "message": "Parse Error"}
        INVALID_REQUEST_ERROR = {"code": -32600, "message": "Invalid Request"}
        METHOD_NOT_FOUND_ERROR = {"code": -32901, "message": "Method not found"}
        INVALID_PARAMS_ERROR = {"code": -32602, "message": "Invalid params"}
        INTERNAL_ERROR = {"code": -32603, "message": "Internal error"}
        

	def onConnection(self, request):
		print("Client connecting: {0}".format(request.peer))

	def onOpen(self):
		print("WebSocket connection open.")
		if "onOpen" in self.msgHandlers:
			self.msgHandlers["onOpen"]()

	def onMessage(self, msg, binary):  # TODO: Support Batch messages
		print "Got message: " + str(msg)
		try:
			if using_encoder:
				msg = json.loads(msg, object_hook=decoder)
			else:
				msg = json.loads(msg)
		except:
			print "Warning: Could not load json."
                        self.__send({"jsonrpcws":ServerProtocolV1.VERSION, "error":ServerProtocolV1.JSON_PARSE_ERROR, "id": None})
			return False
		print msg
		if msg:
			if "method" in msg:
				if msg["method"] in self.msgHandlers:
					self.msgHandlers[msg["method"]](msg)
				else:
					print "Warning: No matching command."
                                        self.send(msg, {"error": ServerProtocolV1.METHOD_NOT_FOUND_ERROR})
			else:   
				print "Warning: No command in message."
                                self.send(msg, {"error": ServerProtocolV1.INVALID_REQUEST_ERROR})
		else:   
			print "Warning: Empty message."
                        self.send(msg, {"error": ServerProtocolV1.INVALID_REQUEST_ERROR})
			return False

	def __send(self, msg):  # this should be private after new send works
		print("Sending... ", msg)
		try:
			if using_encoder:
				msg = json.dumps(msg, cls=Encoder)
			else:
				msg = json.dumps(msg)
		except:
			print "Error: Could not convert object to json."
                        self.__send({"jsonrpcws": ServerProtocolV1.VERSION, "error": ServerProtocolV1.INTERNAL_ERROR, "id": None})  # This could cause a max recursion error because it calls it's self
			raise Exception("Could not convert object to json.")
		print "Sending: " + msg
		self.sendMessage(msg)

        def send(self, request, response, batch=False):
                msg = response.copy()
                if batch:
                        for req, m in zip(request, msg):
                                self.__makeResponse(m, req)
                else:
                        self.__makeResponse(msg, request)

                self.__send(msg)

        def sendError(self, request, error):
                self.send(request, {"error": error})

        def sendResult(self, request, result):
                self.send(request, {"result": result})
                                                    
        def __makeResponse(self, msg, request):
                msg["jsonrpcws"] = ServerProtocolV1.VERSION
                if "id" in request:
                        msg["id"] = request["id"]
                else:
                        msg["id"] = None
                return msg


	def onClose(self, wasClean, code, reason):
                #TODO: Redo this callback
		print("WebSocket connection closed: {0}".format(reason))
		if "onClose" in self.msgHandlers:
			self.msgHandlers["onClose"]({"wasClean": wasClean, "code": code, "reason": reason})
