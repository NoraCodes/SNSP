# Site-local Network Service Protocol (SNSP) Client-server combination.
# Can only emit service announcements, not other types of messages, 
# 	but serves as an illustration of how the system works.

import socket
import struct
import json
import argparse
import time
import logging
from ipaddress import ip_address

parser = argparse.ArgumentParser(description="A simple program which acts as either a client or server for SNSP, the Site-local Network Service Protocol.")
parser.add_argument('-s', '--send', dest='send_mode', action='store_const',
                   const=True, default=False,
                   help='Send packets instead of waiting for them (client instead of server).')
parser.add_argument('--source-address-ip4', dest='source_address_ip4', type=str, default=False, help='The address from which to send packets, or on which to listen for IPv4.')
parser.add_argument('-b4', '--broadcast-address-ip4', dest='broadcast_address_ip4', type=str, default='255.255.255.255', help='The broadcast address to which to should send or from which to recieve packets for IPv4.')
parser.add_argument('--source-address-ip6', dest='source_address_ip6', type=str, default=False, help='The address from which to send packets, or on which to listen for IPv6.')
parser.add_argument('-b46', '--broadcast-address-ip6', dest='broadcast_address_ip6', type=str, default='ff05::', help='The broadcast address to which to should send or from which to recieve packets for IPv6.')
parser.add_argument('-i', dest='interval', type=int, default=60, help="Time, in seconds, between each announcement of services in the services file.")
parser.add_argument('-f', dest='file', type=str, default='services.json', help="Services file to be read.")
parser.add_argument('-l', dest='logfile', type=str, default='', help="File to which to write logs.")

# TODO: Add IPv6

SOURCE_IP4 = ''
SITE_LOCAL_IP4 = ''
SOURCE_IP6 = ''
SITE_LOCAL_IP6 = ''

# Importance values, 0 to 7 from least to most likley to require notifying the user.
IMPORTANCE_ROUTINE = 0 # Messages for network testing, timed updates, etc. Should never be shown to the user.
IMPORTANCE_UTILITY = 1 # Messages for utility purpouses, e.g., SNSP ping
IMPORTANCE_CONFIG = 2  # Messages that might result in network or application configuration changes, but that do not announce a new service 
IMPORTANCE_DEFAULT = 3 # Default. For messages announcing services.
IMPORTANCE_NETANNOUNCE = 4 # Messages about how the network is configured that do NOT require user intervention (i.e., inform devices about optional use of OSPF)
IMPORTANCE_SERVICESTOP = 5 # Messages about cessation of network services - both temporarily and permanently.
IMPORTANCE_USERACTION = 6  # Messages that require user interaction - i.e., revealing captive portal, NETWORK DOWN IN..., etc.
IMPORTANCE_VITAL = 7	   # Messages that absolutely positively must arrive and be shown to the user, if relevant. Possibly place in syslog too.

VERSION = "0.01"

PORT = 81


def NewSNSPMessage(service_name, service_port, host_addr, message, importance = IMPORTANCE_DEFAULT, version = VERSION):
	"""
	Create a new SNSP message.
	"""
	if not isinstance(service_name, str):
		raise ValueError("service_name was not a string.")
		
	if not isinstance(version, str):
		raise ValueError("version was not a string.")
		
	if not isinstance(service_port, int):
		raise ValueError("service_port was not an integer.")
		
	if (not type(importance) is int) or not ((importance >= IMPORTANCE_ROUTINE) and (importance <= IMPORTANCE_VITAL)):
		raise ValueError("Invalid importance value.")
		
	try:
		ip_address(host_addr) # If the address is not really an address, this will fail.
	except ValueError:
		raise ValueError("Address was not a valid IP address.")	
	messagedict = {"version" : version, "service_name" : service_name, \
	"service_port" : service_port, "host_addr" : host_addr, "importance" : importance, "message" : message}
	return messagedict
	
def set_network(source_ip, dest_ip):
	'''
	Change our default source IP and destination IP
	'''
	global SOURCE_IP4
	global SITE_LOCAL_IP4
	SOURCE_IP4 = source_ip
	SITE_LOCAL_IP4 = dest_ip
	
def reset_network():
	'''
	Reset the network settings to the default
	'''
	global SOURCE_IP4
	global SITE_LOCAL_IP4
	SOURCE_IP4 = False # False means use the default interface
	SITE_LOCAL_IP4 = "<broadcast>"
	
def setup_sockets():
	"""
	Set up sockets for TX/RX
	"""
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	if isinstance(SOURCE_IP4, str):
		logging.debug("Setting up socket with a changed network.")
		sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(SOURCE_IP4))
	return sock
		
def teardown_sockets(sock):
	"""
	Tear down our sockets.
	"""
	sock.shutdown()
	sock.close()
		
def SNSP_send(sock, message):
	"""
	Send an SNSP message to all the addresses we have.
	"""
	logging.info("Sending to " + SITE_LOCAL_IP4)
	sock.sendto(bytes(json.dumps(message), 'utf-8'), (SITE_LOCAL_IP4, PORT))
	
	
def SNSP_listen(sock, buf_size=4096):
	"""
	Wait for and return SNSP messages.
	"""
	sock.bind(("", PORT))
	while True:
	    data, addr = sock.recvfrom(0x100)
	    logging.info("received from {0}: {1!r}".format(addr, data))
	
def SNSP_parse(serial_packet):
	"""
	Parse a packet into a dict
	"""
	if not isinstance(serial_packet, str):
		raise ValueError("Tried to SNSP_parse a non-string")
	return json.loads(serial_packet)
	
def load_SNSP_defs_from_file(filename):
	f = open(filename, 'r')
	services = json.load(f)
	#services = []
	#for string in contents_strings:
	#	services.append(SNSP_parse(string))
	f.close()
	return services
		
def dump_SNSP_defs_to_file(filename, services):
	f = open(filename, 'w')
	json.dump(services, f)
	f.close()
	

def __SNSP_serial_print(message):
	print(json.dumps(message))
	return json.dumps(message)
	
def main():
	args = parser.parse_args()
	if not args.logfile is '':
		logging.basicConfig(filename=args.logfile,level=logging.DEBUG)
	else:
		logging.basicConfig(level=logging.DEBUG)
		
	# Verify IP args
	try:
		ip_address(args.broadcast_address_ip4) # If the address is not really an address, this will fail.
	except ValueError:
		raise ValueError("IPv4 broadcast address was not a valid IP address.")	
	
	try:
		ip_address(args.broadcast_address_ip6) # If the address is not really an address, this will fail.
	except ValueError:
		raise ValueError("IPv6 broadcast address was not a valid IP address.")
	
	if args.source_address_ip4 != False:
		try:
			ip_address(args.source_address_ip4) # If the address is not really an address, this will fail.
		except ValueError:
			raise ValueError("IPv4 source address was not a valid IP address.")	
	
	if args.source_address_ip6 != False:
		try:
			ip_address(args.source_address_ip6) # If the address is not really an address, this will fail.
		except ValueError:
			raise ValueError("IPv6 source address was not a valid IP address.")	
			
	global SOURCE_IP4
	global SITE_LOCAL_IP4
	global SOURCE_IP6
	global SITE_LOCAL_IP6
	SOURCE_IP4 = args.source_address_ip4 # False means use the default interface
	SITE_LOCAL_IP4 = args.broadcast_address_ip4
	SOURCE_IP6 = args.source_address_ip6
	SITE_LOCAL_IP6 = args.broadcast_address_ip6
	
	#Listening mode
	if args.send_mode:
		services = load_SNSP_defs_from_file(args.file)
		s = setup_sockets()
		while True:
			for service_message in services:
				SNSP_send(s, service_message)
			time.sleep(args.interval)
	else:
		s = setup_sockets()
		SNSP_listen(s)
	
	
	
if __name__ == "__main__":
	main()
	
	
