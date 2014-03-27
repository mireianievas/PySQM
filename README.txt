PySQM
=====

PySQM is a multi-platform, open-source software designed to read and
plot data from Unihedron SQM-LE and SQM-LU photometers, giving as 
an output files with standard format.

PySQM is distributed under GNU GPL, either version 3 of the License, 
or (at your option) any later version. See the file LICENSE.txt for details.

This software has been developed by Miguel Nievas <miguelnievas@ucm.es> with
the invaluable help of:

 - Jaime Zamorano (UCM)
 - Laura Barbas (OAN)
 - Pablo de Vicente (OAN)


SETUP
=====

After downloading the software, you need to modify the file pysqm/config.py. 
In this file you will find several variables that need to be configured
to match your hardware settings. For example:

 - Position of the observatory.
 - Device identifier.
 - Device address (either IP address for SQM-LE or COM/ttyUSB port).
 - Location of the data files.
 - Axis limits for the plot.

Remember that python (2.7) syntax is mandatory in this file


HOW TO USE THE SOFTWARE
=======================

After configuring the software, make sure you are in the parent directory were
the README, LICENSE and MANIFEST files are located
> ls 
LICENSE.txt  MANIFEST.in  README.txt  pysqm  setup.py

And then run the software.
> python -m pysqm 

The program should find your SQM device and start (if it's night-time) data adquisition.

In some systems, were python3 is the default version of python, you need to specify python2 as
the interpreter to use. This is done usually running it as:

> python2 -m pysqm

or

> python2.7 -m pysqm

Note: running the setup.py script is neither tested nor neccesary at the moment. The program
is currently being redesigned as a normal python package, but at present no setup is required.

