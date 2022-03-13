#!/usr/bin/env python3
#
#  Utilities.py
#
#  Copyright 2022 Harmonicdog. All rights reserved.
#

import math

ZEROdB = float(0x1000) # 12 bit

def LinearInterp(p0, p1, t):
	"""Interpolates linearly between p0 and p1. `t` is a scalar [0,1]"""
	return (1.0-t)*p0 + t*p1
	
def QuadraticInterp(p0, p1, p2, t):
	"""Interpolates quadratically between p0, p1 and p2. `t` is a scalar [0,1]"""
	return (1-t)*(1-t)*p0 + 2*t*(1-t)*p1 + t*t*p2


def ScalarToAmplitude(scalar):
	"""Converts a linear scalar in the range [0,1] to decibels [-45,12] and then to an amplitude scalar"""
	if scalar == 0.0:
		return 0.0
	theDB = LinearInterp(-45.0, 12.0, scalar)
	theAmp = math.pow(10.0, 0.05 * theDB)
	return theAmp

def MMtoDB(mm):
	"""Converts millimeters [0,1] to dB value [-45,12]"""
	return LinearInterp(-45.0, 12.0, mm)
	
def DBtoMM(db):
	"""Converts a dB value [-45,12] to a scalar in millimeters in [0,1]. These are really tiny sliders :)"""
	return (db - -45.0) / (12.0 - -45.0)

def FloatToIntVol(fvol):
	return int(fvol * ZEROdB)

def IntVolToFloat(ivol):
	return ivol / ZEROdB

def Log20k(x):
	return math.log10(x) / 4.301029995663981

def EQIntQtoQ(intq):
	return QuadraticInterp(10.0, 2.0, 1.0, IntVolToFloat(intq))

def EQIntDBtoDB(intdb):
	return IntVolToFloat(intdb) * 18.0
