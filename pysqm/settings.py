#!/usr/bin/env python

'''
PySQM plotting program
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
'''

import os,sys


class ArgParser:
    def __init__(self):
        self.parse_arguments()

    def parse_arguments(self):
        import argparse
        # Return config filename
        parser = argparse.ArgumentParser()
        parser.add_argument('-c', '--config')
        self.args = parser.parse_args()
    
    def get_config_filename(self):
        try:
            assert(self.args.config!=None)
        except:
            configfilename = "config.py"
        else:
            configfilename = self.args.config
        print("Using configuration file: %s." %configfilename)
        return(configfilename)



class ConfigFile:
    def __init__(self, path="config.py"):
        # Guess the selected dir and config filename
        # Should accept:
        # - absolute path (inc. filename)
        # - relative path (inc. filename)
        # - absolute path (exc. filename)
        # - relative path (exc. filename)
        # - shortcouts like ~ . etc
        self.path = path
    
    def read_config_file(self,path):
        # Get the absolute path
        abspath = os.path.abspath(path)
        # Is a dir? Then add config.py (default filename)
        if os.path.isfile(abspath):
            abspath += "/config.py"
        # split directory and filename
        directory = os.path.dirname(abspath)
        filename  = os.path.basename(abspath)

        old_syspath = sys.path
        sys.path.append(directory)
        exec("import %s as config" %filename.split(".")[0])
        self.config = config

# Create an object (by default empty) accessible from everywhere
# After read_config_file is called, GlobalConfig.config will be accessible
GlobalConfig = ConfigFile()
