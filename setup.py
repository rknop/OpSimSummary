#from ez_setup import use_setuptools
#use_setuptools()
#from setuptools import setup, find_packages
from distutils.core import setup

setup(# package information
      name="OpSimSummary",
      version="0.0.1dev",
      description='Simple repo setup to check documentation',
      long_description=''' ''',
      # What code to include as packages
      packages=['OpSimSummary'],
      packagedir={'OpSimSummary':'OpSimSummary'},
      # What data to include as packages
      include_package_data=True,
      package_data={'OpSimSummary':['example_data/*.dat', 'example_data/*.simlib']}
      )
