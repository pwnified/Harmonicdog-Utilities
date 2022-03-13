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

class EQSwapper(NSObject):
	"""EQ settings"""
	
	def __init__(self):
		self._power = False
		self._thresh = FloatToIntVol(1.0)
		self._ratio = FloatToIntVol(0.5)
		self._attack = FloatToIntVol(0.1)
		self._release = FloatToIntVol(0.2)

	def initWithCoder_(self, coder):
		self._power = False
		if coder.containsValueForKey_('power'):
			self._power = coder.decodeBoolForKey_('power')	#power
		self._eqShelfHA = coder.decodeIntForKey_('sHA')	#high shelf amplitude
		self._eqShelfHF = coder.decodeIntForKey_('sHF')	#high shelf frequency
		self._eqShelfLA = coder.decodeIntForKey_('sLA')		#low shelf amplitude
		self._eqShelfLF = coder.decodeIntForKey_('sLF')		#low shelf frequency
		self._eqParametricLQ = coder.decodeIntForKey_('pLQ')	#low Q
		self._eqParametricLF = coder.decodeIntForKey_('pLF')		#low Frequency
		self._eqParametricLA = coder.decodeIntForKey_('pLA')	#low Amplitude
		self._eqParametricHQ = coder.decodeIntForKey_('pHQ')	#high Q
		self._eqParametricHF = coder.decodeIntForKey_('pHF')	#high Frequency
		self._eqParametricHA = coder.decodeIntForKey_('pHA')	#high Amplitude
		return self

	def encodeWithCoder_(self, coder):
		coder.encodeBool_forKey_(self._power, 'power')
		coder.encodeInt_forKey_(self._eqShelfHA, 'sHA')
		coder.encodeInt_forKey_(self._eqShelfHF, 'sHF')
		coder.encodeInt_forKey_(self._eqShelfLA, 'sLA')
		coder.encodeInt_forKey_(self._eqShelfLF, 'sLF')
		coder.encodeInt_forKey_(self._eqParametricLQ, 'pLQ')
		coder.encodeInt_forKey_(self._eqParametricLF, 'pLF')
		coder.encodeInt_forKey_(self._eqParametricLA, 'pLA')
		coder.encodeInt_forKey_(self._eqParametricHQ, 'pHQ')
		coder.encodeInt_forKey_(self._eqParametricHF, 'pHF')
		coder.encodeInt_forKey_(self._eqParametricHA, 'pHA')
		
	def get_power(self):
		return 'ON' if self._power else 'OFF'

	@python_method
	def get_pLF(self):
		lll = QuadraticInterp(Log20k(50.0), Log20k(250.0), Log20k(1500.0), IntVolToFloat(self._eqParametricLF))
		return math.pow(20000.0, lll)

	@python_method
	def get_pHF(self):
		lll = LinearInterp(Log20k(450.0), 1.0, IntVolToFloat(self._eqParametricHF))
		return math.pow(20000.0, lll)

	@python_method
	def description(self, samplerate):
		return '%s (sHA: %.1f) (sHF: %d) (sLA: %.1f) (sLF: %d) (pLQ: %.3f) (pLF: %.3f) (pLA: %.1f) (pHQ: %.3f) (pHF: %.3f) (pHA: %.1f)' % (self.get_power(), EQIntDBtoDB(self._eqShelfHA), self._eqShelfHF, EQIntDBtoDB(self._eqShelfLA), self._eqShelfLF, EQIntQtoQ(self._eqParametricLQ), self.get_pLF(), EQIntDBtoDB(self._eqParametricLA), EQIntQtoQ(self._eqParametricHQ), self.get_pHF(), EQIntDBtoDB(self._eqParametricHA));
