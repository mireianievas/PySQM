#!/usr/bin/env python

'''
PySQM reading program
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
__version__ = "2.4"
__maintainer__ = "Miguel Nievas"
__email__ = "miguelnr89[at]gmail[dot]com"
__status__ = "Development" # "Prototype", "Development", or "Production"


import os,sys
import inspect
import time,signal
import math
import datetime
import ephem
import numpy as np
import struct

from .read import *

# Read the config variables from pysqm.config.py
import pysqm.config
import pysqm.plot
Options = pysqm.config.__dict__
Keys = Options.keys()
Values = Options.values()
Items = Options.items()

# Import config variables
for index in xrange(len(Items)):
	if "__" not in str(Items[index][0]):
		exec("from pysqm.config import "+str(Items[index][0]))


'''
This import section is only for software build purposes.
Dont worry if some of these are missing in your setup.
'''

def relaxed_import(themodule):
	try: exec('import '+str(themodule))
	except: pass

relaxed_import('socket')
relaxed_import('serial')
relaxed_import('_mysql')
relaxed_import('pysqm.email')

'''
Conditional imports
'''

# If the old format (SQM_LE/SQM_LU) is used, replace _ with -
_device_type = _device_type.replace('_','-')

if _device_type == 'SQM-LE':
	import socket
elif _device_type == 'SQM-LU':
	import serial
if _use_mysql == True:
	import _mysql


# Create directories if needed
for directory in [monthly_data_directory,daily_data_directory,current_data_directory]:
	if not os.path.exists(directory):
		os.makedirs(directory)





if __name__ == '__main__':
	'''
	Select the device to be used based on user input
	and start the measures
	'''

	if _device_type=='SQM-LU':
		mydevice = SQMLU()
	elif _device_type=='SQM-LE':
		mydevice = SQMLE()
	else:
		print('ERROR. Unknown device type '+str(_device_type))
		exit(0)

	'''
	Ephem is used to calculate moon position (if above horizon)
	and to determine start-end times of the measures
	'''
	observ = define_ephem_observatory()
	niter = 0
	DaytimePrint=True

	print('Starting readings ...')
	while 1<2:
		''' The programs works as a daemon '''
		utcdt = mydevice.read_datetime()
		#print (str(mydevice.local_datetime(utcdt))),
		if mydevice.is_nighttime(observ):
			StartDateTime = datetime.datetime.now()
			niter += 1

			mydevice.define_filenames()

			''' Get values from the photometer '''
			try:
				timeutc_mean,timelocal_mean,temp_sensor,\
				freq_sensor,ticks_uC,sky_brightness = \
					mydevice.read_photometer(\
					 Nmeasures=_measures_to_promediate,PauseMeasures=10)
			except:
				#raise
				print('Connection lost')
				if _reboot_on_connlost == True:
					sleep(600)
					os.system('reinicio_programado.bat')

				#print('Reseting device')
				mydevice.reset_device()
				continue

			formatted_data = mydevice.format_content(\
				timeutc_mean,timelocal_mean,temp_sensor,\
				freq_sensor,ticks_uC,sky_brightness)

			if _use_mysql == True: mydevice.save_data_mysql(formatted_data)
			mydevice.data_cache(formatted_data,number_measures=_cache_measures)

			if niter%_plot_each == 0:
				''' Each X minutes, plot a new graph '''
				try: pysqm.plot.make_plot(send_emails=False,write_stats=False)
				except:
					print('Warning: Error plotting data.')
					print(sys.exc_info())


			if DaytimePrint==False:
				DaytimePrint=True

			MainDeltaSeconds = (datetime.datetime.now()-StartDateTime).total_seconds()
			time.sleep(max(1,_delay_between_measures-MainDeltaSeconds))

		else:
			''' Daytime, print info '''
			if DaytimePrint==True:
				utcdt = utcdt.strftime("%Y-%m-%d %H:%M:%S")
				print (utcdt),
				print('. Daytime. Waiting until '+str(mydevice.next_sunset(observ)))
				DaytimePrint=False
			if niter>0:
				mydevice.flush_cache()
				if _send_data_by_email==True:
					try: pysqm.plot.make_plot(send_emails=True,write_stats=True)
					except:
						print('Warning: Error plotting data / sending email.')
						print(sys.exc_info())

				else:
					try: pysqm.plot.make_plot(send_emails=False,write_stats=True)
					except:
						print('Warning: Error plotting data.')
						print(sys.exc_info())

				niter = 0
			time.sleep(300)


