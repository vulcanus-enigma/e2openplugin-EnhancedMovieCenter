#!/usr/bin/python
# encoding: utf-8
#
# CutListSupport
# Copyright (C) 2011 cmikula, betonme
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
import struct
from bisect import insort

from enigma import eServiceReference
from Screens.InfoBarGenerics import InfoBarCueSheetSupport, InfoBarSeek

from EMCTasker import emcDebugOut
from IsoFileSupport import IsoSupport


# Cut File support class
# Description
# http://git.opendreambox.org/?p=enigma2.git;a=blob;f=doc/FILEFORMAT
class CutList():
	#__shared_state = {}
	
	# InfoBarCueSheetSupport types
	CUT_TYPE_IN = 0
	CUT_TYPE_OUT = 1
	CUT_TYPE_MARK = 2
	CUT_TYPE_LAST = 3
	# Additional types
	CUT_TYPE_SAVEDLAST = 4
	
	# Additional cut_list information
	#		cut_list[x][0] = pts   = long long
	#		cut_list[x][1] = what  = long
	
	# Constants
	ENABLE_RESUME_SUPPORT = True
	MOVIE_FINISHED = 0xFFFFFFFFFFFFFFFF

	def __init__(self, service=None, borg=False):
		#if borg:
		#	self.__dict__ = self.__shared_state
		if not '_ready' in dir(self):
			# Very first one time initialization
			self._ready = True
			
			# Is already initialized in InfoBar and EMCMediaCenter
			#InfoBarCueSheetSupport.__init__(self)
			#InfoBarSeek.__init__(self)
						
			self.cut_file = None
			self.cut_mtime = 0
			self.cut_list = []
			self.iso = None
		
		self.__newService(service)
		self.__readCutFile()

	def __newService(self, service):
		path = None
		name = None
		if service and isinstance(service, eServiceReference):
			path = service.getPath()
			if path.endswith(".iso"):
				if not self.iso:
					self.iso = IsoSupport(service, borg=True)
				name = self.iso and self.iso.getIsoName()
				if name and len(name):
					path = "/home/root/dvd-" + name
			elif os.path.isdir(path):
				path += "/dvd"
			path += ".cuts"
			if self.cut_file != path:
				#print "[EMC CUTS] __newService IF " + str(path)
				self.cut_file = path
				self.cut_mtime = 0
			#else:
			#	print "[EMC CUTS] __newService ELSE " + str(path)
		else:
			# No service or no eServiceReference
			#print "[EMC CUTS] __newService No service or no eServiceReference" + str(service)
			self.cut_file = None
			self.cut_mtime = 0
			self.cut_list = []
			self.iso = None

	def __ptsToSeconds(self, pts):
		# Cut files are using the presentation time stamp time format
		# pts has a resolution of 90kHz
		return pts / 90 / 1000

	def __secondsToPts(self, seconds):
		return seconds * 90 * 1000

	##############################################################################
	## Overwrite Functions 

	# InfoBarCueSheetSupport
	def downloadCuesheet(self):
		try:
			# Is there native cuesheet support
			cue = InfoBarCueSheetSupport._InfoBarCueSheetSupport__getCuesheet(self)
			if cue:
				# Native cuesheet support
				self.cut_list = cue.getCutList()
			else:
				# No native cuesheet support
				self.__newService(self.service)
				self.__readCutFile()
		except Exception, e:
			emcDebugOut("[CUTS] downloadCutList exception:" + str(e))

	# InfoBarCueSheetSupport
	def uploadCuesheet(self):
		try:
			# Is there native cuesheet support
			cue = InfoBarCueSheetSupport._InfoBarCueSheetSupport__getCuesheet(self)
			if cue:
				# Native cuesheet support
				cue.setCutList(self.cut_list)
			else:
				# No native cuesheet support
				self.__newService(self.service)
				self.__writeCutFile()
		except Exception, e:
			emcDebugOut("[CUTS] uploadCutList exception:" + str(e))

	##############################################################################
	## Get Functions
	def getCutList(self):
		return self.cut_list
	
	def getCutListMTime(self):
		return self.cut_mtime
		
	# Wrapper in seconds 
	def getCutListLast(self):
		return self.__ptsToSeconds( self.__getCutListLast() )

	def getCutListLength(self):
		return self.__ptsToSeconds( self.__getCutListLength() )

	def getCutListSavedLast(self):
		return self.__ptsToSeconds( self.__getCutListSavedLast() )
		
	# Intenal from cutlist in pts
	def __getCutListLast(self):
		if self.cut_list:
			for (pts, what) in self.cut_list:
				if what == self.CUT_TYPE_LAST:
					return pts
		return 0

	def __getCutListLength(self):
		if self.cut_list:
			for (pts, what) in self.cut_list:
				if what == self.CUT_TYPE_OUT:
					return pts
		return 0

	def __getCutListSavedLast(self):
		if self.cut_list:
			for (pts, what) in self.cut_list:
				if what == self.CUT_TYPE_SAVEDLAST:
					return pts
		return 0

	##############################################################################
	## Modify Functions
	## Use remove and insort to guarantee the cut list is sorted

	# API modification functions
	# Calculate in seconds
	# A modification will always be written immediately
	def toggleLastCutList(self, toggle=0): #, saveLast=False):
		# toggle > 0 : toggle
		# toggle = 0 : 0
		# toggle < 0 : saved
		self.__toggleLast( toggle) #, saveLast )
		self.__writeCutFile()

	def updateCutList(self, play, length):
		self.__removePTS( self.__getCutListSavedLast() )
		self.__replaceLast( play )
		self.__replaceOut( length )
		self.__writeCutFile()

	def removeMarksCutList(self):
		# All Marks will be removed
		# All others items will stay
		if self.cut_list:
			for cp in self.cut_list[:]:
				if cp[1] == self.CUT_TYPE_MARK:
					self.cut_list.remove(cp)
		self.__writeCutFile()

	# Internal modification functions
	# Calculate in pts
	# Without saving changes
	def __toggleLast(self, toggle): #, saveLast):
		try:
			oldLast = self.__getCutListLast()
			savedLast = self.__getCutListSavedLast()
			newLast = 0
			newSaved = 0
			
			if toggle > 0:
				newLast = self.MOVIE_FINISHED
			elif toggle == 0:
				newLast = 0
			elif toggle < 0:
				if savedLast == oldLast:
					newLast = self.MOVIE_FINISHED
				else:
					newLast = savedLast or self.MOVIE_FINISHED
			
			newSaved = savedLast or oldLast
		
			self.__removePTS(savedLast)
			self.__replaceLast(newLast)
			#if saveLast:
			self.__insortSavedLast(newSaved)
		except Exception, e:
			emcDebugOut("[CUTS] uploadCuesheet exception:" + str(e))

	def __replaceOut(self, pts):
		if self.cut_list:
			for cp in self.cut_list[:]:
				if cp[1] == self.CUT_TYPE_OUT:
					self.cut_list.remove(cp)
		if pts > 0:
			insort(self.cut_list, (pts, self.CUT_TYPE_OUT))

	def __replaceLast(self, pts):
		if self.cut_list:
			for cp in self.cut_list[:]:
				if cp[1] == self.CUT_TYPE_LAST:
					self.cut_list.remove(cp)
		if pts > 0:
			insort(self.cut_list, (pts, self.CUT_TYPE_LAST))

	def __insortSavedLast(self, pts):
		if pts > 0 and pts < self.MOVIE_FINISHED:
			insort(self.cut_list, (pts, self.CUT_TYPE_MARK))
			insort(self.cut_list, (pts, self.CUT_TYPE_SAVEDLAST))

	def __removePTS(self, pts):
		if self.cut_list:
			for cp in self.cut_list[:]:
				if cp[0] == pts:
					if cp[1] == self.CUT_TYPE_SAVEDLAST or cp[1] == self.CUT_TYPE_MARK:  # or cp[1] == self.CUT_TYPE_LAST
						self.cut_list.remove(cp)

	##############################################################################
	## File IO Functions
	def __readCutFile(self):
		try:
			data = ""
			path = self.cut_file
			if path and os.path.exists(path):
				mtime = os.path.getmtime(path)
				if self.cut_mtime == mtime:
					# File has not changed
					#print "[EMC CUTS] __readCutFile PASS " + str(path)
					pass
					
				else:
					# New Service or file has changed
					#print "[EMC CUTS] __readCutFile " + str(path) + " " + str(self.cut_mtime) + " " + str(mtime)
					self.cut_mtime = mtime
					
					# Read data from file
					# OE1.6 with Pyton 2.6
					#with open(path, 'rb') as f: data = f.read()	
					f = None
					try:
						f = open(path, 'rb')
						data = f.read()
					except Exception, e:
						emcDebugOut("[CUTS] Exception in __readCutFile: " + str(e))
					finally:
						if f is not None:
							f.close()
							
					# Parse and unpack data
					if data:
						pos = 0
						while pos+12 <= len(data):
							# Unpack
							(pts, what) = struct.unpack('>QI', data[pos:pos+12])
							insort(self.cut_list, (long(pts), what))
							# Next cut_list entry
							pos += 12
					else:
						# No date clear all
						self.cut_list = []
						#print "[EMC CUTS] __readCutFile NO DATA " + str(path)
			else:
				# No path or no file clear all
				self.cut_list = []
				#print "[EMC CUTS] __readCutFile NO FILE " + str(path)
				
		except Exception, e:
			emcDebugOut("[CUTS] __readCutFile exception:" + str(e))

	def __writeCutFile(self):
		try:
			data = ""
			path = self.cut_file
			if path:
			
				# Generate and pack data
				if self.cut_list:
					for (pts, what) in self.cut_list:
						data += struct.pack('>QI', pts, what)
						
				# Write data to file
				# OE1.6 with Pyton 2.6
				#with open(path, 'wb') as f: f.write(data)
				f = None
				try:
					f = open(path, 'wb')
					if data:
						f.write(data)
				except Exception, e:
					emcDebugOut("[CUTS] Exception in __writeCutFile: " + str(e))
				finally:
					if f is not None:
						f.close()
				
				# Save file timestamp
				if path and os.path.exists(path):
					self.cut_mtime = os.path.getmtime(path)
				
		except Exception, e:
			emcDebugOut("[CUTS] __writeCutFile exception:" + str(e))
			
