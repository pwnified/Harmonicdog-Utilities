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
		self.pan = coder.decodeIntForKey_('pan2') / 4096.0			# [-1:1]
		self.send = coder.decodeIntForKey_('send2a') / 4096.0		# [0:1]
		self.volumeDB = LinearInterp(-45.0, 12.0, self.volume)		# [-45:12]
		return self

	def encodeWithCoder_(self, coder):
		coder.encodeInt_forKey_(self.volume * 4096.0, 'vol2')
		coder.encodeInt_forKey_(self.pan * 4096.0, 'pan2')
		coder.encodeInt_forKey_(self.send * 4096.0, 'send2a')



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
			self.fadeA0 = coder.decodeFloatForKey_('fadeA0')
			self.fadeA1 = coder.decodeFloatForKey_('fadeA1')
			self.fadeB0 = coder.decodeFloatForKey_('fadeB0')
			self.fadeB1 = coder.decodeFloatForKey_('fadeB1')
		else:
			self.fadeA = 128
			self.fadeB = 128
			self.fadeA0 = 1.0/3
			self.fadeA1 = 2.0/3
			self.fadeB0 = 1.0/3
			self.fadeB1 = 2.0/3
		return self

	def encodeWithCoder_(self, coder):
		coder.encodeInt_forKey_(self.binID, 'binID')
		coder.encodeObject_forKey_(self.name, 'name')
		coder.encodeInt_forKey_(self.realStart, 'realStart')
		coder.encodeInt_forKey_(self.realLength, 'realLength')
		coder.encodeInt_forKey_(self.binStart, 'binStart')
		coder.encodeInt_forKey_(self.fadeA, 'fadeA')
		coder.encodeInt_forKey_(self.fadeB, 'fadeB')
		coder.encodeFloat_forKey_(self.fadeA0, 'fadeA0')
		coder.encodeFloat_forKey_(self.fadeA1, 'fadeA1')
		coder.encodeFloat_forKey_(self.fadeB0, 'fadeB0')
		coder.encodeFloat_forKey_(self.fadeB1, 'fadeB1')



class VirtualTrack(NSObject):
	"""Holds a list of VirtualRegions"""
	
	def initWithCoder_(self, coder):
		count = coder.decodeIntForKey_('numRegions')
		self.regions = [coder.decodeObjectForKey_('region %d' % i) for i in range(count)]
		return self

	def encodeWithCoder_(self, coder):
		coder.encodeInt_forKey_(len(self.regions), 'numRegions')
		[coder.encodeObject_forKey_(self.regions[i], 'region %d' % i) for i in range(len(self.regions))]



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
	
	def encodeWithCoder_(self, coder):
		coder.encodeObject_forKey_(self.friendlyName, 'friendlyName')
		coder.encodeInt_forKey_(self.trackNum, 'trackNum')
		coder.encodeInt_forKey_(self.orderNum, 'orderNum')
		coder.encodeInt_forKey_(self.numChannels, 'numChannels')
		coder.encodeObject_forKey_(self.virtualTrack, 'virtualTrack')
		coder.encodeBool_forKey(self.muted, 'muted')
		coder.encodeBool_forKey(self.soloed, 'soloed')
		coder.encodeObject_forKey_(self.controlValues, 'controlValues')


class BinHolder:
	"""Metadata for a wav is encoded into the filename of the wav file. This class
	parses the filename (without the .wav extension) and fills out the class
	"""
	def __init__(self, hexstring):
		binstring = binascii.unhexlify(hexstring)
		self.version = int(struct.unpack('>B', binstring[0:1])[0])
		if self.version == 1:
			# B = version		(location 0, length 1)
			# H = binID		(location 1, length 2)
			# B = channels	(location 3, length 1)
			# i = samples	(location 4, length 4)
			# Q = hash		(location 8, length 8)
			# I = offset		(location 16, length 4)
			# c = name		(location 20, length extends to end)
			binID, channels, samples, hash, offset = struct.unpack('>HBiQI', binstring[1:20])
			name = binstring[20:]
			bytesPerChannel = 2 #16 bit
			bitrateFormat = 5 # 44100
		elif self.version == 2:
			# B = version		(location 0, length 1)
			# H = binID		(location 1, length 2)
			# B = channels	(location 3, length 1)
			# i = samples	(location 4, length 4)
			# B = bytesPerChannel (location 8, length 1)
			# B = bitrateFormat (location 9, length 1)
			# Q = hash		(location 10, length 8)
			# I = offset		(location 18, length 4)
			# c = name		(location 22, length extends to end)
			binID, channels, samples, bytesPerChannel, bitrateFormat, hash, offset = struct.unpack('>HBiBBQI', binstring[1:22])
			name = binstring[22:]
		else:
			raise ValueError('unsupported version on bin filename: %d' % self.version)

		self.binID = int(binID)
		self.channels = int(channels)
		self.samples = int(samples)
		self.bitsPerSample = int(bytesPerChannel) * 8
		self.sampleRate = self.BitrateFormatToSamplerate(bitrateFormat)
		self.hash = int(hash)
		self.offset = int(offset)
		self.name = name
			
	def Print(self):
		print '[binID %d] [name: \"%s\"] [channels: %d] [samples: %d] [bps: %d] [rate: %d] [offset: %d] [hash: 0x%016x]' % (self.binID, self.name, self.channels, self.samples, self.bitsPerSample, self.sampleRate, self.offset, self.hash)

	def BitrateFormatToSamplerate(self, bitrateFormat):
		bitrates = { 0: 0, 1: 11025, 2: 12000, 3: 22050, 4: 24000, 5: 44100, 6: 48000, 7: 88200, 8: 96000 }
		return bitrates[bitrateFormat]

def main(argv):
	"""
	Print some data about the MultiTrack DAW song project and exit.
	Call this script with a single argument, which is the path to the song directory.
	Which should be a relative path from the current directory.
		e.g
		ReadProject.py "../../My Songs/Song 1/"
	"""
	
	if len(argv) <= 1:
		raise ValueError('Usage: ReadProject.py "../../My Songs/Song 1/"')
	
	songPath = os.path.normpath(os.path.join(os.getcwd(), argv[1]))
	if not os.path.isdir(songPath):
		raise ValueError('Bad input song folder: %s' % songPath)

	tracksFile = os.path.join(songPath, 'Tracks2.plist')
	if not os.path.isfile(tracksFile):
		tracksFile = os.path.join(songPath, 'Tracks.plist')
	if not os.path.isfile(tracksFile):
		raise ValueError('Not a song project: %s' % songPath)

	projectFile = os.path.join(songPath, 'project.plist')
	if not os.path.isfile(projectFile):
		raise ValueError('Missing project.plist file: %s' % songPath)

	try:
		tracks = NSKeyedUnarchiver.unarchiveObjectWithFile_(tracksFile)
	except:
		raise ValueError('Some problem with %s' % tracksFile)


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




if __name__ == '__main__':
	main(sys.argv)




