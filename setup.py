from setuptools import setup

setup(name='RackScanner',
      version='0.1',
      description='Application for reading racks of DataMatrix barcoded tubes.',
      url='http://github.com/michalkahle/RackScanner',
      author='Michal Kahle',
      author_email='michalkahle@gmail.com',
      license='MIT',
      py_modules=['dm_reader', 'http_server', 'scanner_controller', 'web_app'],
      zip_safe=False)
