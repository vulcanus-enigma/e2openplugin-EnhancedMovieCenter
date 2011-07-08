#!/usr/bin/python
# encoding: utf-8
#
# Suomipoeka plugin by moveq
# Copyright (C) 2007-2010 moveq / Suomipoeka team (suomipoeka@gmail.com)
#
# New Codes added and Bugfixed by Coolman & Swiss-MAD
#
# In case of reuse of this source code please do not remove this copyright.
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	For more information on the GNU General Public License see:
#	<http://www.gnu.org/licenses/>.
#
import os
from Components.Network import iNetwork
from EMCTasker import spDebugOut
from DelayedFunction import DelayedFunction


class NetworkAwareness:
	def __init__(self):
		self.retries = 0
		self.ip = None
		self.initialized = False

	def whatIsMyIP(self):
		if not self.initialized: self.ipLookup()
		return self.ip

	def ipLookup(self):
		os.system("ifconfig | grep Bcast | sed 's;^.*addr:;;' | sed 's: .*::' >/tmp/myip")
		file = open("/tmp/myip")
		myip = file.read()
		file.close()
		self.ip = [ int(a) for a in myip.split(".") ]
		if len(self.ip) != 4:
			self.ip = [0,0,0,0]
		else:
			self.initialized = True
		spDebugOut( "[spNET] IP = " + str(self.ip).replace(", ", ".")[1:-1] )

spNET = NetworkAwareness()
