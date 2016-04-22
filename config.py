#!/usr/bin/env python

'''
PySQM configuration File.
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
Notes:

You may need to change the following variables to match your
observatory coordinates, instrumental properties, etc.

Python (v2.7) syntax is mandatory.
____________________________
'''


'''
-------------
SITE location
-------------
'''
_observatory_name = 'OBS_NAME'
_observatory_latitude  = 0
_observatory_longitude = 0
_observatory_altitude  = 0
# If Sun is below this altitude, the program will take data
_observatory_horizon   = 10

# Device (short)name for filenames
_device_shorttype = 'SQM'
# Device type. SQM_LE / SQM_LU
_device_type = 'SQM_LE'
# Long Device name. Should include the name of the observatory.
_device_id = _device_type + '-' + _observatory_name
# Device location in the world
_device_locationname = 'Locality/State/Country - Observatory Name'
# Data supplier (contact)
_data_supplier = 'Supplier Name / Institution'
# Default Adress of the device
# Can be either an IP Adress (p.e. 169.254.1.13) in SQM-LE or a COM port (p.e. COM13) in SQM-LU
_device_addr = '169.254.1.13'
# Take the mean of N measures to remove jitter
_measures_to_promediate = 5
# Delay between two measures. In seconds.
_delay_between_measures = 5
# Get N measures before writing on screen/file
_cache_measures = 5
# Call the plot function each N measures.
_plot_each = 60


'''
-------------------------------------
TimeZone of the site and the computer
-------------------------------------
'''

# The real timezone of the site (without daylight saving)
_local_timezone     = +1
# Reboot if we loose connection
_reboot_on_connlost = False

'''
------------------
Device calibration
------------------
'''

# magnitude = read_magnitude + offset
_offset_calibration  = -0.11
# Correct the offset in the plot?
_plot_corrected_data = False

'''
---------------------------------------
System PATHs to save the data and plots
---------------------------------------
'''

# Monthly (permanent) data
monthly_data_directory = "/Path/To/SQM/Data"
# Daily (permanent) data
daily_data_directory   = monthly_data_directory+"/daily_data/"
# Daily (permanent) graph
daily_graph_directory = monthly_data_directory+"/daily_plots/"
# Current data, deleted each day.
current_data_directory = monthly_data_directory
# Current graph, deleted each day.
current_graph_directory = monthly_data_directory
# Summary with statistics for the night
summary_data_directory = monthly_data_directory

'''
----------------------------
PySQM data center (OPTIONAL)
----------------------------
'''

# Send the data to the data center (NOT available yet!)
_send_to_datacenter = False

'''
---------------------------------
MYSQL database options (OPTIONAL)
---------------------------------
'''

# Set to True if you want to store data on a MySQL db.
_use_mysql = False
# Host (ip:port / localhost) of the MySQL engine.
_mysql_host = None
# User with write permission on the db.
_mysql_user = None
# Password for that user.
_mysql_pass = None
# Name of the database.
_mysql_database = None
# Name of the database table
_mysql_dbtable = None
# Port of the MySQL server.
_mysql_port = None



'''
---------------
Ploting options
---------------
'''
# Plot only date / full plot (datetime + sun alt)
full_plot  = False
# Limits in Y-axis of the plot (Night Sky Background)
limits_nsb = [15,22]
# Time (hours) for the beginning and the end of the session. (LOCALTIME)
limits_time   = [17,9]
# Limits in the Sun altitude for the plot. In degrees.
limits_sunalt = [-90,5]



'''
-------------
Email options
-------------
'''
# Requires pysqm.email.py module. Not released yet!.
_send_data_by_email = False

