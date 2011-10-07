from setuptools import setup, find_packages
import sys, os

version = '0.9'

setup(name='stdcli',
      version=version,
      description="fixme",
      long_description="""fixme""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='dell',
      author='Michael Brown',
      author_email='Michael_E_Brown@Dell.com',
      url='',
      license='LGPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points={
        'console_scripts': [ 'stdcli_test = stdcli.stdcli_test:main', ],
        'stdcli_cli_extensions': [
            'sample = stdcli.plugins.builtin:SamplePlugin',
            'dump-config = stdcli.plugins.builtin:DumpConfigPlugin',
            ],
        },
      )
