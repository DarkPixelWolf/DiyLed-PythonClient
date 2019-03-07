from uuid import getnode as get_mac
import socket
import struct
from http.server import BaseHTTPRequestHandler
import socketserver
import threading
import time
import json

import board
import neopixel

class DeviceProperties:
	def __init__(self, name, leds, state, brightness, mode, modes, r, g, b):
		self.name = name
		self.leds = leds
		self.state = state
		self.brightness = brightness
		self.mode = mode
		self.modes = modes
		self.r = r
		self.g = g
		self.b = b
		
	def get_ip(self):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		try:
			#doesn't even have to be reachable
			s.connect(('10.255.255.255', 1))
			IP = s.getsockname()[0]
		except:
			IP = '127.0.0.1'
		finally:
			s.close()
		return IP
		
	def assembleJson(self):
		jsonData = {
			"id": "createRequestPacket",
			"data": {
				"request": "light",
				"id": hex(get_mac()),
				"name": self.name,
				"ip": str(self.get_ip()),
				"ledCount": self.leds,
				"power": str(bool(self.state)).lower(),
				"brightness": self.brightness,
				"mode": self.mode,
				"modes": self.modes,
				"color": [self.r, self.g, self.b]
			}
		}
		return json.dumps(jsonData)

class DiyLedClient:
	def __init__(self, valueCallback, stateGetCallback, DEBUG = False):
		self.valueCallback = valueCallback
		self.stateGetCallback = stateGetCallback
		self.DEBUG = DEBUG
		self.MCAST_GRP = '239.255.255.250'
		self.MCAST_PORT = 1900
		
	def startUDPServer(self):
		self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.udp.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32) 
		self.udp.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
		self.udp.bind((self.MCAST_GRP, self.MCAST_PORT))
		host = socket.gethostbyname(socket.gethostname())
		self.udp.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(host))
		mreq = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)
		self.udp.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)	
		
	class HTTPServer(socketserver.TCPServer):
		def server_bind(self):
			self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.socket.bind(self.server_address)
		
	class httpHandler(BaseHTTPRequestHandler):
		outer = None	
		def do_GET(self):
			path = str(self.path)
			print(path)
			if (path == "/diyled"):
				self.outer.servePage(self)
				return
			elif (path == "/properties"):
				self.outer.serveProperties(self)
				return
			elif (path.startswith("/api")):
				content_len = int(self.headers.get('Content-Length', 0))
				post_body = self.rfile.read(content_len)
				# handle
				return
			else:
				if (self.outer.DEBUG):
					print("Not-Found HTTP call:")
					print("URI: " + path)
					content_len = int(self.headers.get('Content-Length', 0))
					post_body = self.rfile.read(content_len)
					print("Body: " + str(post_body))
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				self.wfile.write(("Not Found (diyled-internal)").encode('utf-8'))
				return
			self.send_response(200)
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			self.wfile.write(("ERROR").encode('utf-8'))
			return
			
		def do_PUT(self):
			path = str(self.path)
			print(path)
			if (path.startswith("/diyledapi")):
				content_len = int(self.headers.get('Content-Length', 0))
				post_body = self.rfile.read(content_len)
				if (post_body):
					self.outer.handleApiCall(path, post_body.decode('utf-8'), self)
				
	def servePage(self, handler):
		if (self.DEBUG):
			print("HTTP Req ...")
		res = "DiyLed Client V1.1 for python!\r\n\r\n"
		res += "\r\n\r\DiyLed Client v1.1 by Sebastian Scheibe 2019"
		handler.send_response(200)
		handler.send_header('Content-type', 'text/plain')
		handler.end_headers()
		handler.wfile.write(res.encode('utf-8'))
		
	def serveProperties(self, handler):
		if (self.DEBUG):
			print("# Responding to properties ... #")
		localIP = self.get_ip()
		
		setup_json = self.stateGetCallback().assembleJson()
		if (self.DEBUG):
			print("Sending: " + setup_json)
		handler.send_response(200)
		handler.send_header('Content-type', 'application/json')
		handler.end_headers()
		handler.wfile.write(setup_json.encode('utf-8'))
		
	def startHTTPServer(self):
		self.httpHandler.outer = self
		self.server = self.HTTPServer(('', 80), self.httpHandler)
		tServer = threading.Thread(target = self.server.serve_forever)
		tServer.daemon = True
		tServer.start()
		
	def get_ip(self):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		try:
			#doesn't even have to be reachable
			s.connect(('10.255.255.255', 1))
			IP = s.getsockname()[0]
		except:
			IP = '127.0.0.1'
		finally:
			s.close()
		return IP
		
	def respondToSearch(self, request_addr):
		localIP = self.get_ip()
		response = "\r\n".join([
			'HTTP/1.1 200 OK',
			'EXT:',
			'CACHE-CONTROL: max-age=100',
			'LOCATION: http://' + localIP + ':80/properties',
			'SERVER: DiyLed/1.1, UPnP/1.0, DiyLedLight/1.1',
			'ST: urn:diyleddevice:light',
			'USN: uuid:' + str(hex(get_mac())) + '::urn:diyleddevice','', ''])
		ip, port = request_addr
		self.udp.sendto(response.encode('utf-8'), (ip, self.MCAST_PORT))
		
	def handleApiCall(self, req, data, handler):
		response = ""
		if not json.loads(data):
			response = {
				"id": "errorPacket",
				"data": {
					"message": "Ungueltige Daten.",
					"id": "UNKNOWN"
				}
			}	
		else:
			data = json.loads(data)
			if (req.find("/updateValue") > 0):
				self.valueCallback(data["data"]["key"], data["data"]["value"])
				response = {
					"id": "successPacket",
					"data": {
						"message": "Wert geaendert.",
						"id": data["data"]["id"]
					}
				}
			elif (req.find("/applyScene") > 0):
				self.valueCallback("brightness", data["data"]["brightness"])
				self.valueCallback("mode", data["data"]["mode"])
				self.valueCallback("color", data["data"]["color"])
				self.valueCallback("power", data["data"]["power"])
				response = {
					"id": "successPacket",
					"data": {
						"message": "Werte geaendert.",
						"id": data["data"]["id"]
					}
				}
			else:
				response = {
					"id": "errorPacket",
					"data": {
						"message": "Ungueltige Anfrage.",
						"id": data["data"]["id"]
					}
				}	
		handler.send_response(200)
		handler.send_header('Content-type', 'application/json')
		handler.end_headers()
		handler.wfile.write(json.dumps(response).encode('utf-8'))
			
	
	def begin(self):
		self.startUDPServer()
		self.startHTTPServer()
		
	def loop(self):
		request, request_addr = self.udp.recvfrom(1024)
		request = request.decode('utf-8')
		#if (self.DEBUG):
		#	print(request)
		if (request):
			if (request.find("M-SEARCH") >= 0):
				if (request.find("urn:diyleddevice") > 0):
					if (self.DEBUG):
						print(request)
						print("Responding search req...")
					self.respondToSearch(request_addr)
	
