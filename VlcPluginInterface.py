#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2011 by Coolman & Swiss-MAD
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

from enigma import eServiceReference
from EMCTasker import emcDebugOut


class VlcFileListWrapper:
	def __init__(self):
		pass
	def getNextFile(self):
		return None, None
	def getPrevFile(self):
		return None, None


class VlcPluginInterfaceSel():
	def browsingVLC(self):
		return self.currentPathSel.find("VLC servers") > 0

	def vlcMovieSelected(self, entry):
		try:
			self.hide()
#			from Plugins.Extensions.VlcPlayer.VlcPlayer import VlcPlayer
#			dlg = self.session.open(VlcPlayer, self["list"].vlcServer, VlcFileListWrapper())
#			dlg.playfile(entry[4], entry[3])
			try:	# v2.5
				self["list"].vlcServer.play(self, entry[4], entry[3], VlcFileListWrapper())
			except:	# v2.6
				self["list"].vlcServer.play(self.session, entry[4], entry[3], VlcFileListWrapper())
			self.wasClosed = True
			self.close()
		except Exception, e:
			emcDebugOut("[spVLC] vlcMovieSelected exception:\n" + str(e))


class VlcPluginInterfaceList():
	def currentSelIsVlc(self):
		try:	return self.list[self.getCurrentIndex()][2] == "VLCs"
		except:	return False

	def currentSelIsVlcDir(self):
		try:	return self.list[self.getCurrentIndex()][1] == "VLCd"
		except:	return False

	def reloadVlcServers(self):
		try:
			from Plugins.Extensions.VlcPlayer.VlcServerConfig import vlcServerConfig
			self.vlcServers = vlcServerConfig.getServerlist()	# settings change requires running this
			self.list = []
			sref = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + "..")	# dummy ref
			self.list.append((sref, None, None, None, "..", None, 0, ""))
			for srv in self.vlcServers:
				srvName = srv.getName()
				sref = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + srvName)	# dummy ref
				self.list.append((sref, "VLCd", None, None, srvName, None, 0, ""))
			self.list.sort(key=lambda x: x[1],reverse=False)
			self.l.setList(self.list)
		except:	pass

	def reloadVlcFilelist(self):
		self.list = []
		sref = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + "..")	# dummy ref
		self.list.append((sref, None, None, None, "..", None, 0, ""))

		vlcPath = self.loadPath[self.loadPath.find("VLC servers/")+12:]	# server/dir/name/
		serverName = vlcPath.split("/")[0]
		emcDebugOut("[spML] path on %s = %s" %(serverName, vlcPath))
		server = None
		self.vlcServer = None
		for srv in self.vlcServers:
			if srv.getName() == serverName: server = srv	# find the server
		if server is not None:
			try:
				self.vlcServer = server
				emcDebugOut("[spML] baseDir = " + server.getBasedir())
				vlcPath = vlcPath[len(serverName):]
				emcDebugOut("[spML] vlcPath = " + vlcPath)
				(vlcFiles, vlcDirs) = server.getFilesAndDirs(server.getBasedir() + vlcPath, None)
				emcDebugOut("[spML] got files and dirs...")
				for d in vlcDirs:
					if d[0] == "..": continue
					sref = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + d[0])	# dummy ref
					self.list.append((sref, "VLCd", None, None, d[0], None, 0, ""))
				for f in vlcFiles:
					from Plugins.Extensions.VlcPlayer.VlcFileList import MEDIA_EXTENSIONS
					from MovieCenter import mediaExt
					global mediaExt
					ext = os.path.splitext(f[0])[1].lower()
					if MEDIA_EXTENSIONS.has_key(ext) or ext in mediaExt:
						sref = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + f[0])	# dummy ref
						self.list.append((sref, None, "VLCs", f[0], f[1], None, 0, ext))
			except Exception, e:
				emcDebugOut("[spML] reloadVlcFilelist exception:\n" + str(e))
		#self.list.sort(key=lambda x: x[1],reverse=False)
		self.l.setList(self.list)

