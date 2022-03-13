#!/usr/bin/env python3
#
#  Copyright 2022 Harmonicdog. All rights reserved.
#


#pip install pyobjc
from Foundation import *
#import objc
from objc import python_method
import math
from Utilities import *

class CompSwapper(NSObject):
	"""Compressor settings"""
	
	def __init__(self):
		self._power = False
		self._thresh = FloatToIntVol(1.0)
		self._ratio = FloatToIntVol(0.5)
		self._attack = FloatToIntVol(0.1)
		self._release = FloatToIntVol(0.2)

	def initWithCoder_(self, coder):
		self._power = False
		if coder.containsValueForKey_('power'):
			self._power = coder.decodeBoolForKey_('power')
		self._thresh = coder.decodeIntForKey_('thresh')
		self._ratio = coder.decodeIntForKey_('ratio')
		self._attack = coder.decodeIntForKey_('attack')
		self._release = coder.decodeIntForKey_('release')
		return self

	def encodeWithCoder_(self, coder):
		coder.encodeBool_forKey_(self._power, 'power')
		coder.encodeInt_forKey_(self._thresh, 'thresh')
		coder.encodeInt_forKey_(self._ratio, 'ratio')
		coder.encodeInt_forKey_(self._attack, 'attack')
		coder.encodeInt_forKey_(self._release, 'release')

	def get_power(self):
		return 'ON' if self._power else 'OFF'
	

	def get_thresh(self):
		return LinearInterp(-45.0, 0.0, IntVolToFloat(self._thresh))

	def get_ratio(self):
		return LinearInterp(1/100.0, 1.0, IntVolToFloat(self._ratio));

	@python_method
	def get_attack(self, samplerate):
		ms = QuadraticInterp(0.1, 10.0, 400.0, IntVolToFloat(self._attack));
		theAttack = math.exp(-1000.0 / (ms * samplerate))
		return theAttack

	@python_method
	def get_release(self, samplerate):
		ms = QuadraticInterp(1.0, 100.0, 2000.0, IntVolToFloat(self._release));
		theRelease = math.exp(-1000.0 / (ms * samplerate))
		return theRelease

	@python_method
	def description(self, samplerate):
		return '%s (thresh: %.3f) (ratio: %.2f:1) (attack: %.3f) (release: %.3f)' % (self.get_power(), self.get_thresh(), 1.0/self.get_ratio(), self.get_attack(samplerate), self.get_release(samplerate))
