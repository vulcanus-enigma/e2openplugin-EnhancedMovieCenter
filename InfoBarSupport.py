#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2011 by betonme
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

from Components.config import *
from Components.ActionMap import ActionMap, NumberActionMap, HelpableActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from enigma import eTimer, iPlayableService, iServiceInformation, eServiceReference, iServiceKeys, getDesktop
from Screens.Screen import Screen
from Screens.InfoBarGenerics import *
from Screens.InfoBar import InfoBar
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen
from Tools.Directories import fileExists

from EnhancedMovieCenter import _
from EMCTasker import emcDebugOut
from DelayedFunction import DelayedFunction
#from CutListSupport import CutList


class InfoBarSupport(	InfoBarShowHide, \
											InfoBarMenu, \
											InfoBarBase, \
											InfoBarSeek, \
											InfoBarShowMovies, \
											InfoBarAudioSelection, \
											InfoBarNumberZap, \
											InfoBarNotifications, \
											InfoBarSimpleEventView, \
											InfoBarServiceNotifications, \
											InfoBarTeletextPlugin, \
											InfoBarPVRState, \
											InfoBarCueSheetSupport, \
											InfoBarMoviePlayerSummarySupport, \
											InfoBarSubtitleSupport, \
											InfoBarServiceErrorPopupSupport, \
											InfoBarExtensions, \
											InfoBarPlugins ):

	def __init__(self):
		
		for x in 	InfoBarShowHide, \
							InfoBarMenu, \
							InfoBarBase, \
							InfoBarSeek, \
							InfoBarShowMovies, \
							InfoBarAudioSelection, \
							InfoBarNumberZap, \
							InfoBarNotifications, \
							InfoBarSimpleEventView, \
							InfoBarServiceNotifications, \
							InfoBarTeletextPlugin, \
							InfoBarPVRState, \
							InfoBarCueSheetSupport, \
							InfoBarMoviePlayerSummarySupport, \
							InfoBarSubtitleSupport, \
							InfoBarServiceErrorPopupSupport, \
							InfoBarExtensions, \
							InfoBarPlugins:
			x.__init__(self)

	##############################################################################
	## Override from InfoBarGenerics.py
	
	# InfoBarCueSheetSupport
	def jumpNextMark(self):
		if not self.jumpPreviousNextMark(lambda x: x-90000):
			# There is no further mark
			self.doSeekEOF()
		else:
			if config.usage.show_infobar_on_skip.value:
				# InfoBarSeek
				self.showAfterSeek()

	def playLastCB(self, answer):
		if answer == True:
			self.doSeek(self.resume_point)
		# DVDPlayer Workaround
		self.pauseService()
		self.unPauseService()

	# InfoBarSeek
	def doEof(self):
		self.setSeekState(self.SEEK_STATE_PLAY)

	def doSeekRelative(self, pts):
		if self.getSeekLength() < self.getSeekPlayPosition() + pts:
			# Relative jump is behind the movie length
			self.doSeekEOF()
		else:
			# Call baseclass function
			InfoBarSeek.doSeekRelative(self, pts)

	def getSeekPlayPosition(self):
		try:
			# InfoBarCueSheetSupport
			return self.cueGetCurrentPosition()
		except Exception, e:
			emcDebugOut("[EMCMC] getSeekPlayPosition exception:" + str(e))
			return 0

	def getSeekLength(self):
		try:
			# Call private InfoBarCueSheetSupport function
			seek = InfoBarCueSheetSupport._InfoBarCueSheetSupport__getSeekable(self)
		except Exception, e:
			emcDebugOut("[EMCMC] getSeekLength exception:" + str(e))
		if seek is None:
			return None
		len = seek.getLength()
		return long(len[1])

	# Handle EOF
	def doSeekEOF(self):
		try:
			# Stop one second before eof : 1 * 90 * 1000
			pts = self.getSeekLength() - 90000
			if pts > 0:
				# InfoBarSeek
				self.doSeek(pts)
			# Wait one second before signaling eof
			# Call private InfoBarSeek function
			DelayedFunction(1000, InfoBarSeek._InfoBarSeek__evEOF, self)
		except Exception, e:
			emcDebugOut("[EMCMC] doSeekEOF exception:" + str(e))
	
