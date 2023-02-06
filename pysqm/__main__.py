#!/usr/bin/env python

'''
PySQM __main__ code
____________________________

Copyright (c) Mireia Nievas <mnievas[at]ucm[dot]es>

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
'''

#from types import ModuleType
#import sys

import pysqm.main as main

while(1==1):
    # Loop forever to make sure the program does not die.
    try:
        main.loop()
    except Exception as e:
        print('')
        print('FATAL ERROR while running the main loop !!')
        print('Error was:')
        print(e)
        print('Trying to restart')
        print('')

