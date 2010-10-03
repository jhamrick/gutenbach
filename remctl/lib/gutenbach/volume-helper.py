#!/usr/bin/python

from __future__ import division
from subprocess import *
import sys
import math
import time
import os
j = os.path.join

arg = sys.argv[1]
currentDir = os.path.split(__file__)[0]
#sys.path[:0] = [currentDir]

def getVolume():
	"""
		Returns current PCM volume percentage as int
	"""
	v = int(Popen(j(currentDir,'volume-get'), stdout=PIPE).communicate()[0].split()[0])
	return v

def setVolume(percent):
	"""
		Over the course of 3 seconds, in steps of 0.3sec, linearly sets
		volume between [current vol]-->[new vol]
	"""
	v = getVolume()
	newV = percent
	for i in range(10+1):
		frac = i/10
		tempV = int(v + (newV-v)*frac)
		command = ['amixer', 'set', 'PCM', str(tempV)]
		#print tempV
		sys.stdout.flush()
		call(command, stdout=PIPE)
		time.sleep(0.3)

v = getVolume()
map = {
        '+': int(math.ceil( v*1.13 + .001 )),
        '-': int(math.floor( v/1.13 + .001 ))
}

newVolume = map[arg]

# Alert user
print 'Smoothly modifying over next 3 seconds, by ~3dB (from %i to %i)...' % (v, newVolume)
sys.stdout.flush()

# Adjust volume
setVolume(newVolume)

# Alert user
print 'Volume adjust finished.'

# Send zephyr
call([j(currentDir,'volume-zephyr')])

