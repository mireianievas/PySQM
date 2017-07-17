#!/usr/bin/env python

from distutils.core import setup

setup(name='pysqm',
      version='3.1',
      author='Mireia Nievas',
      author_email='mnievas@ucm.es',
      url='http://guaix.fis.ucm.es/hg/pysqm/',
      license='GPLv3',
      description='SQM reading and plotting software',
      packages=['pysqm'],
      install_requires=['pyephem','numpy','matplotlib']
      classifiers=[
                   "Programming Language :: C",
                   "Programming Language :: Cython",
                   "Programming Language :: Python :: 2.7",
                   "Programming Language :: Python :: Implementation :: CPython",
                   'Development Status :: 3 - Alpha',
                   "Environment :: Other Environment",
                   "Intended Audience :: Science/Research",
                   "License :: OSI Approved :: GNU General Public License (GPL)",
                   "Operating System :: OS Independent",
                   "Topic :: Scientific/Engineering :: Astronomy",
                   ],
      long_description=open('README.txt').read()
      )
