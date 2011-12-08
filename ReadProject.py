#!/usr/bin/env python
#
#  ReadProject.py
#  MultiTrack
#
#  Created by Hamilton Feltman on 12/07/11.
#  Copyright 2011 Harmonicdog. All rights reserved.
#

import sys, os, binascii, struct, string, fileinput
from Foundation import *

def LinearInterp(p0, p1, t):
	"""Interpolates linearly between p0 and p1. `t` is the scalar in the range [0:1]"""
	return (1.0-t)*p0 + t*p1

def ScalarToAmplitude(scalar):
	"""Converts a linear scalar in the range [0:1] to decibels [-45:+12] and then to an amplitude scalar"""
	if scalar == 0.0:
		return 0.0
	theDB = LinearInterp(-45.0, 12.0, scalar)
	theAmp = 10.0 ** (0.05 * theDB)
	return theAmp

class TrackControlPoint(NSObject):
	"""Holds a volume, pan, and send scalar"""
	def initWithCoder_(self, coder):
		self.volume = coder.decodeIntForKey_('vol2') / 4096.0		# [0:1]
		self.volumeDB = LinearInterp(-45.0, 12.0, self.volume)		# [-45:12]
		self.pan = coder.decodeIntForKey_('pan2') / 4096.0			# [-1:1]
		self.send = coder.decodeIntForKey_('send2a') / 4096.0		# [0:1]
		return self

class VirtualRegion(NSObject):
	"""Contains region information for a single region"""
	def initWithCoder_(self, coder):
		self.binID = coder.decodeIntForKey_('binID')
		self.name = coder.decodeObjectForKey_('name')
		self.realStart = coder.decodeIntForKey_('realStart')
		self.realLength = coder.decodeIntForKey_('realLength')
		self.binStart = coder.decodeIntForKey_('binStart')
		if coder.containsValueForKey_('fadeA'):
			self.fadeA = coder.decodeIntForKey_('fadeA')
			self.fadeB = coder.decodeIntForKey_('fadeB')
		return self

class VirtualTrack(NSObject):
	"""Holds a list of VirtualRegions"""
	def initWithCoder_(self, coder):
		numRegions = coder.decodeIntForKey_('numRegions')
		self.regions = [coder.decodeObjectForKey_('region %d' % i) for i in range(numRegions)]
		return self
	

class CacheTrack(NSObject):
	"""Holds information about a track"""
	def initWithCoder_(self, coder):
		self.friendlyName = coder.decodeObjectForKey_('friendlyName')
		self.trackNum = coder.decodeIntForKey_('trackNum')
		self.orderNum = coder.decodeIntForKey_('orderNum')
		self.numChannels = coder.decodeIntForKey_('numChannels')
		self.virtualTrack = coder.decodeObjectForKey_('virtualTrack')
		self.muted = coder.decodeBoolForKey_('muted')
		self.soloed = coder.decodeBoolForKey_('soloed')
		self.controlValues = coder.decodeObjectForKey_('controlValues')
		return self
	


class BinHolder:
	"""Metadata for a wav is encoded into the filename of the wav file. This class
	parses the filename (without the .wav extension) and fills out the class
	"""
	def __init__(self, hexstring):
		# v = version		(location 0, length 1)
		# i = binID			(location 1, length 2)
		# c = channels		(location 3, length 1)
		# s = samples		(location 4, length 4)
		# h = hash			(location 8, length 8)
		# o = offset		(location 16, length 4)
		# n = name			(location 20, length extends to end)
		binstring = binascii.unhexlify(hexstring)
		self.version = int(struct.unpack('>B', binstring[0:1])[0])
		if self.version == 1:
			binID, channels, samples, hash, offset = struct.unpack('>HBiQI', binstring[1:20])
			self.binID = int(binID)
			self.channels = int(channels)
			self.samples = int(samples)
			self.hash = int(hash)
			self.offset = int(offset)
			self.name = binstring[20:]
		else:
			print 'unsupported version: %d' % self.version

	def Print(self):
		print '[binID %d] [name: \"%s\"] [channels: %d] [samples: %d] [offset: %d] [hash: 0x%016x]' % (self.binID, self.name, self.channels, self.samples, self.offset, self.hash)


if __name__ == '__main__':
	"""
	Print some data about the MultiTrack DAW song project and exit.
	Call this script with a single argument, which is the path to the song directory.
	Which should be a relative path from the current directory.
		e.g
		ReadProject.py "../../My Songs/Song 1/"
	"""
	
	if len(sys.argv) <= 1:
		raise BaseException('Missing Song Folder argument')
	
	songPath = os.path.normpath(os.path.join(os.getcwd(), sys.argv[1]))
	if not os.path.isdir(songPath):
		raise BaseException('Bad input song folder: %s' % songPath)

	tracksFile = os.path.join(songPath, 'Tracks.plist')
	if not os.path.isfile(tracksFile):
		raise BaseException('Not a song project: %s' % songPath)

	projectFile = os.path.join(songPath, 'project.plist')
	if not os.path.isfile(projectFile):
		raise BaseException('Missing project.plist file: %s' % songPath)

	try:
		tracks = NSKeyedUnarchiver.unarchiveObjectWithFile_(tracksFile)
	except:
		raise BaseException('Some problem with %s' % tracksFile)


	print '\nPROJECT:'
	project = NSDictionary.dictionaryWithContentsOfFile_(projectFile)
	print '   projectVersion: %d' % project['projectVersion']
	print '   inputVolumeDB: %f' % project['inputVolumeDB']
	print '   outputVolumeDB: %f' % project['outputVolumeDB']
	print '   metronomeVolume: %f' % project['metronomeVolume']
	print '   tempo: %f' % project['tempo']



	print '\nTRACKS: %d' % len(tracks)
	for track in tracks:
		print 'TRACK %d: \"%s\"' % (track.orderNum, track.friendlyName)
		print '   [numChannels: %d] [muted: %s] [soloed: %s] [volumeDB: %f] [pan: %f] [send: %f]' % (track.numChannels, track.muted, track.soloed, track.controlValues.volumeDB, track.controlValues.pan, track.controlValues.send)
		print '   REGIONS: %d' % len(track.virtualTrack.regions)
		for region in track.virtualTrack.regions:
			print '      [name: \"%s\"] [binID: %d] [realStart: %d] [realLength: %d] [binStart: %d]' % (region.name, region.binID, region.realStart, region.realLength, region.binStart)

	binPath = os.path.join(songPath, 'Bins')
	binNames = os.listdir(binPath)

	print '\nBINS:'
	for binName in binNames:
		if string.lower(binName[-4:]) == '.wav':
			hexstring = binName[:-4]
			BinHolder(hexstring).Print()


