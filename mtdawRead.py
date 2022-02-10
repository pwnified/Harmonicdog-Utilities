#!/usr/bin/env python3
#
#  mtdawRead.py
#  MultiTrack
#
#  Copyright 2019 Harmonicdog. All rights reserved.
#

import sys, os, binascii, struct, string, fileinput, operator

#pip install pyobjc
from Foundation import *

#pip install crcmod
import crcmod
crc = crcmod.mkCrcFun(0x142F0E1EBA9EA3693, rev=False, initCrc=0x0, xorOut=0xFFFFFFFFFFFFFFFF)


def LinearInterp(p0, p1, t):
	"""Interpolates linearly between p0 and p1. `t` is the scalar [0,1]"""
	return (1.0-t)*p0 + t*p1

def ScalarToAmplitude(scalar):
	"""Converts a linear scalar in the range [0,1] to decibels [-45,12] and then to an amplitude scalar"""
	if scalar == 0.0:
		return 0.0
	theDB = LinearInterp(-45.0, 12.0, scalar)
	theAmp = 10.0 ** (0.05 * theDB)
	return theAmp

def DBtoMM(db):
	"""Converts a dB value [-45,12] to a scalar in millimeters in [0,1]. These are really tiny sliders :)"""
	return (db - -45.0) / (12.0 - -45.0)


class TrackControlPoint(NSObject):
	"""Holds a volume, pan, and send scalar"""

	def initWithCoder_(self, coder):
		self.volume = coder.decodeIntForKey_('vol2') / 4096.0		# [0,1]
		self.pan = coder.decodeIntForKey_('pan2') / 4096.0			# [-1,1]
		self.send = coder.decodeIntForKey_('send2a') / 4096.0		# [0,1]
		self.volumeDB = LinearInterp(-45.0, 12.0, self.volume)		# [-45,12]
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
		self.realStart = coder.decodeIntForKey_('realStart') # absolute sample along timeline of where this region starts
		self.realLength = coder.decodeIntForKey_('realLength') # length of region
		self.binStart = coder.decodeIntForKey_('binStart') # offset in samples into Bin
		if coder.containsValueForKey_('volume'):
			self.volume = coder.decodeFloatForKey_('volume') # -45 to +12 scaled to [0,1]
		else:
			self.volume = DBtoMM(0)
		if coder.containsValueForKey_('fadeA'):
			self.fadeA = coder.decodeIntForKey_('fadeA') # offset relative to start, ie. realStart + fadeA
			self.fadeB = coder.decodeIntForKey_('fadeB') # offset relative to end, ie. (realStart+realLength) - fadeB
		else:
			self.fadeA = 128
			self.fadeB = 128
		return self

	def encodeWithCoder_(self, coder):
		coder.encodeInt_forKey_(self.binID, 'binID')
		coder.encodeObject_forKey_(self.name, 'name')
		coder.encodeInt_forKey_(self.realStart, 'realStart')
		coder.encodeInt_forKey_(self.realLength, 'realLength')
		coder.encodeInt_forKey_(self.binStart, 'binStart')
		coder.encodeFloat_forKey_(self.volume, 'volume')
		coder.encodeInt_forKey_(self.fadeA, 'fadeA')
		coder.encodeInt_forKey_(self.fadeB, 'fadeB')


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
		self.trackHue = coder.decodeFloatForKey_('trackHue')
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
		coder.encodeFloat_forKey_(self.trackHue, 'trackHue')

class BinHolder:
	"""Metadata for a wav is encoded into the filename of the wav file. This class
	parses the filename (without the .wav extension) and fills out the class
	"""
	def __init__(self, fullpath):
		if str.lower(fullpath[-4:]) == '.wav':
			self.fullpath = fullpath
			binName = os.path.basename(fullpath)
			hexstring = binName[:-4]
		else:
			return None
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
		print ('   [binID %d] [channels: %d] [samples: %d] [bps: %d] [rate: %d] [offset: %d] [hash: 0x%016x] [name: %s]' % (self.binID, self.channels, self.samples, self.bitsPerSample, self.sampleRate, self.offset, self.hash, self.name))

	def BitrateFormatToSamplerate(self, bitrateFormat):
		bitrates = { 0: 0, 1: 11025, 2: 12000, 3: 22050, 4: 24000, 5: 44100, 6: 48000, 7: 88200, 8: 96000 }
		return bitrates[bitrateFormat]

	def CalculateHash(self):
		"""Open the bin and read 'samples' of data starting at 'offset', hash it, and compare to the
			hash stored in the metadata. Assumes data is contiguous. frameSize is
			bytes per sample (2 or 3) * number of channels (1 or 2)
		"""
		hash = 0
		f = open(self.fullpath, 'rb')
		if f:
			frameSize = (self.bitsPerSample // 8) * self.channels
			f.seek(self.offset)
			remaining = self.samples * frameSize
			while remaining > 0:
				toread = min(remaining, 1024*1024)
				data = f.read(toread)
				remaining -= toread
				hash = crc(data, hash)
		return hash

def Read(songPath):
	if not os.path.isdir(songPath):
		raise ValueError('Bad input mtdaw project: %s' % songPath)
	tracksFile = os.path.join(songPath, 'Tracks2.plist')
	if not os.path.isfile(tracksFile):
		tracksFile = os.path.join(songPath, 'Tracks.plist')
	if not os.path.isfile(tracksFile):
		raise ValueError('Not a song project: %s' % songPath)
	projectFile = os.path.join(songPath, 'project.plist')
	if not os.path.isfile(projectFile):
		raise ValueError('Missing project.plist file: %s' % songPath)
	tracks = NSKeyedUnarchiver.unarchiveObjectWithFile_(tracksFile)
	project = NSDictionary.dictionaryWithContentsOfFile_(projectFile)
	return tracks, project

def SignatureForIndex(x):
	signatures = { 0:(2,2), 1:(2, 4), 2:(3, 4), 3:(4, 4), 4:(5, 4), 5:(7, 4), 6:(6, 8), 7:(7, 8), 8:(9, 8), 9:(11, 8), 10:(12, 8) }
	return signatures[x]


def main(argv):
	"""Print some data about the mtdaw song project and exit.
		Call this script with a single argument, the path to the mtdaw project.
		Should be a relative path from the current directory.
		e.g
		mtdawRead.py ../Songs/BbMin7.mtdaw
	"""
	if len(argv) <= 1:
		exit('Usage: %s song.mtdaw' % argv[0])

	songPath = os.path.normpath(os.path.join(os.getcwd(), argv[1]))
	tracks, project = Read(songPath)
	print ('\n-------------------------------------------------------------------------------------------------------')
	print ('PROJECT:', argv[1])
	print ('   projectVersion: %d' % project['projectVersion'])
	print ('   inputVolumeDB: %.1f' % project['inputVolumeDB'])
	print ('   outputVolumeDB: %.1f' % project['outputVolumeDB'])
	if project.objectForKey_('metronomeVolume'):
		print ('   metronomeVolume: %.1f' % project['metronomeVolume'])
	print ('   tempo: %.1f' % project['tempo'])
	sigIndex = project.get('timeSignature2', project.get('timeSignature', 3))
	numerator, denominator = SignatureForIndex(sigIndex)
	print ('   timeSignature: [Index: %d] ["%d/%d"]' % (sigIndex, numerator, denominator))

	print ('\nTRACKS [count: %d]' % len(tracks))
	for track in sorted(tracks, key=operator.attrgetter('orderNum')):
		print ('TRACK [orderNum: %d] [name: "%s"]' % (track.orderNum, track.friendlyName))
		print ('   [numChannels: %d] [muted: %s] [soloed: %s] [volumeDB: %.1f] [pan: %f] [send: %.4f] [trackHue: %f]' % (track.numChannels, track.muted, track.soloed, track.controlValues.volumeDB, track.controlValues.pan, track.controlValues.send, track.trackHue))
		print ('   REGIONS [count: %d]' % len(track.virtualTrack.regions))
		for region in track.virtualTrack.regions:
			print ('      [binID: %d] [realStart: %d] [realLength: %d] [binStart: %d] [fadeA: %d] [fadeB: %d] [volume: %f] [name: "%s"]' % (region.binID, region.realStart, region.realLength, region.binStart, region.fadeA, region.fadeB, region.volume, region.name))

	binPath = os.path.join(songPath, 'Bins')
	binNames = os.listdir(binPath)

	print ('\nBINS:')
	for binName in binNames:
		holder = BinHolder(os.path.join(binPath, binName))
		if holder != None:
			holder.Print()
			h = holder.CalculateHash()
			if h != holder.hash:
				print("Failed hash:", hex(h))

			

	print ('\n')

if __name__ == '__main__':
	main(sys.argv)




