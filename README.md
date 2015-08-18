SNSP
----

The Site-local Network Service Protocol - example scripts and definitions

SNSP is a way to advertise network services over IPv4 broadcast and (WIP) IPv6 multicast.

An SNSP "packet" is just some JSON in a UDP broadcast (or in IPv6, multicast). It contains:

	Service name and specifications (host, port)
	Timestamp
	Importance (a value from 0 to 7, explained below)
	A message (arbitrary text, for, e.g., announcing captive portals in a import. 6 message to be shown to the user.)
	
	If service name is "__user__" and both port and host are 0, the message should be shown to the user if it is of sufficient importance.
	
	
Importance values:

IMPORTANCE_ROUTINE (0):			Messages for network testing, timed updates, etc. Should never be shown to the user.
IMPORTANCE_UTILITY (1): 		Messages for utility purpouses, e.g., SNSP ping
IMPORTANCE_CONFIG (2):  		Messages that might result in network or application configuration changes, but that do not announce a new service 
IMPORTANCE_DEFAULT (3): 		Default. For messages announcing services.
IMPORTANCE_NETANNOUNCE (4):		Messages about how the network is configured that do NOT require user intervention (i.e., inform devices about optional use of OSPF)
IMPORTANCE_SERVICESTOP (5):		Messages about cessation of network services - both temporarily and permanently.
IMPORTANCE_USERACTION (6):		Messages that require user interaction - i.e., revealing captive portal, NETWORK DOWN IN..., etc.
IMPORTANCE_VITAL (7):			Messages that absolutely positively must arrive and be shown to the user, if there is one. Possibly place in syslog too.

