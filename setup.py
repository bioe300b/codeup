import os
os.environ["MLPCONFIGDIR"] = "."

from setuptools import setup, find_packages

setup(  name = 'bioe300b',
        version = '0.1',
        description = 'Library for BioE 300B code submission',
        packages = find_packages(exclude=['Doc']),
        url = 'https://github.com/zasexton/codeup',
        download_url = 'https://github.com/zasexton/codeup', 
        authors = 'Zack Sexton',
        license = 'GPL2',
        install_requires = ['requests'],
        zip_safe = True )
