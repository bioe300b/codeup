from setuptools import setup, find_packages

setup(  name = 'bioe300b',
        version = '0.02',
        description = 'Library for BioE 300B code submission',
        packages = find_packages(exclude=['Doc']),
        url = 'https://github.com/bioe300b/codeup',
        download_url = 'https://github.com/bioe300b/codeup', 
        authors = 'Paul Nuyujukian',
        license = 'GPL2',
        install_requires = ['requests'],
        zip_safe = True )
