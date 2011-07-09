#!/usr/bin/python
# encoding: utf-8
#
# EitSupport
# Copyright (C) 2011 betonme
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

from EMCTasker import emcDebugOut

import os

# Eit File support class
# Description
# http://de.wikipedia.org/wiki/Event_Information_Table
class EitList():
	def __init__(self, service=None):
		#self.serviceReference = service
		if service:
			self.eit_file = service.getPath() + ".eit"
			self.readEitFile()

	##############################################################################
	## File IO Functions
	def readEitFile(self):
		try:
			# Read data from file
			data = ""
			if os.path.exists(self.eit_file):
#TODO R or RB
				with open(self.eit_file, 'rb') as file:
					data = file.read()	

			# Parse and unpack data
			if data:
				# Parse data
				pass
#TODO
		except Exception, e:
			emcDebugOut("[EIT] readEitFile exception:" + str(e))

	def writeEitFile(self):
		# Generate and pack data
		data = ""
		if self.eit_file:
#TODO
			pass
		# Write data to file
		if os.path.exists(self.eit_file):
#TODO w or wb
			with open(self.eit_file, 'wb') as file:
				file.write(data)

	##############################################################################
	## Get Functions
#TODO
		
	# Wrapper
#TODO
