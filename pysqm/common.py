#!/usr/bin/env python

'''
PySQM common code
____________________________

Copyright (c) Miguel Nievas <miguelnievas[at]ucm[dot]es>

This file is part of PySQM.

PySQM is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PySQM is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with PySQM.  If not, see <http://www.gnu.org/licenses/>.

____________________________

Requirements:
 - Python 2.7
 - Pyephem
 - Numpy
 - Socket (for SQM-LE). It should be part of standard python install.
 - Serial (for SQM-LU)
 - python-mysql to enable DB datalogging [optional].

____________________________
'''

__author__ = "Miguel Nievas"
__copyright__ = "Copyright (c) 2014 Miguel Nievas"
__credits__ = [\
 "Miguel Nievas @ UCM",\
 "Jaime Zamorano @ UCM",\
 "Laura Barbas @ OAN",\
 "Pablo de Vicente @ OAN"\
 ]
__license__ = "GNU GPL v3"
__shortname__ = "PySQM"
__longname__ = "Python Sky Quality Meter pipeline"
__version__ = "0.1"
__maintainer__ = "Miguel Nievas"
__email__ = "miguelnievas[at]ucm[dot]es"
__status__ = "Development" # "Prototype", "Development", or "Production"


import sys
import math
import ephem
import signal
import datetime
import time

# Read the config variables from pysqm.config.py
import pysqm.config
Options = pysqm.config.__dict__
#Options.pop('__builtins__')
Keys = Options.keys()
Values = Options.values()
Items = Options.items()

# Import config variables
for index in xrange(len(Items)):
	if "__" not in str(Items[index][0]):
		exec("from pysqm.config import "+str(Items[index][0]))


def define_ephem_observatory():
	''' Define the Observatory in Pyephem '''
	OBS = ephem.Observer()
	OBS.lat = _observatory_latitude*ephem.pi/180
	OBS.lon = _observatory_longitude*ephem.pi/180
	OBS.elev = _observatory_altitude
	return(OBS)

def remove_linebreaks(data):
	# Remove line breaks from data
	data = data.replace('\r\n','')
	data = data.replace('\r','')
	data = data.replace('\n','')
	return(data)

def format_value(data,remove_str=' '):
	# Remove string and spaces from data
	data = remove_linebreaks(data)
	data = data.replace(remove_str,'')
	data = data.replace(' ','')
	return(data)

def format_value_list(data,remove_str=' '):
	# Remove string and spaces from data array/list
	data = [format_value(line,remove_str).split(';') for line in data]
	return(data)

def set_decimals(number,dec=3):
		str_number = str(number)
		int_,dec_ = str_number.split('.')
		while len(dec_)<=dec:
			dec_=dec_+'0'

		return(int_+'.'+dec_[:dec])

class observatory(object):
	def read_datetime(self):
		# Get UTC datetime from the computer.
		utc_dt = datetime.datetime.utcnow()
		#utc_dt = datetime.datetime.now() - datetime.timedelta(hours=_computer_timezone)
                #time.localtime(); daylight_saving=_.tm_isdst>0
		return(utc_dt)

	def local_datetime(self,utc_dt):
		# Get Local datetime from the computer, without daylight saving.
		return(utc_dt + datetime.timedelta(hours=_local_timezone))

	def calculate_sun_altitude(self,OBS,timeutc):
		# Calculate Sun altitude
		OBS.date = ephem.date(timeutc)
		Sun = ephem.Sun(OBS)
		return(Sun.alt)

	def next_sunset(self,OBS):
		# Next sunset calculation
		previous_horizon = OBS.horizon
		OBS.horizon = str(_observatory_horizon)
		next_setting = OBS.next_setting(ephem.Sun()).datetime()
		next_setting = next_setting.strftime("%Y-%m-%d %H:%M:%S")
		OBS.horizon = previous_horizon
		return(next_setting)

	def is_nighttime(self,OBS):
		# Is nightime (sun below a given altitude)
		timeutc = self.read_datetime()
		if self.calculate_sun_altitude(OBS,timeutc)*180./math.pi>_observatory_horizon:
			return False
		else:
			return True



RAWHeaderContent = '''# Definition of the community standard for skyglow observations 1.0
# URL: http://www.darksky.org/NSBM/sdf1.0.pdf
# Number of header lines: 35
# This data is released under the following license: ODbL 1.0 http://opendatacommons.org/licenses/odbl/summary/
# Device type: $DEVICE_TYPE
# Instrument ID: $DEVICE_ID
# Data supplier: $DATA_SUPPLIER
# Location name: $LOCATION_NAME
# Position: $OBSLAT, $OBSLON, $OBSALT
# Local timezone: $TIMEZONE
# Time Synchronization: NTP
# Moving / Stationary position: STATIONARY
# Moving / Fixed look direction: FIXED
# Number of channels: 1
# Filters per channel: HOYA CM-500
# Measurement direction per channel: 0., 0.
# Field of view: 20
# Number of fields per line: 6
# SQM serial number: $SERIAL_NUMBER
# SQM firmware version: $FEATURE_NUMBER
# SQM cover offset value: $OFFSET
# SQM readout test ix: $IXREADOUT
# SQM readout test rx: $RXREADOUT
# SQM readout test cx: $CXREADOUT
# Comment:
# Comment:
# Comment:
# Comment:
# Comment: Capture program: PySQM
# blank line 30
# blank line 31
# blank line 32
# UTC Date & Time, Local Date & Time, Temperature, Counts, Frequency, MSAS
# YYYY-MM-DDTHH:mm:ss.fff;YYYY-MM-DDTHH:mm:ss.fff;Celsius;number;Hz;mag/arcsec^2
# END OF HEADER
'''
