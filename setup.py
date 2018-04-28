#! /usr/bin/env python
#
import os
# temporarily redirect config directory to prevent matplotlib importing
# testing that for writeable directory which results in sandbox error in
# certain easy_install versions
os.environ["MPLCONFIGDIR"] = "."

DESCRIPTION = "Astetik data visualization and reporting library"
LONG_DESCRIPTION = """\

astetik provides a very high level overlay on Seaborn and matplotlib.
It is a data visualization library for data exploration, and for
telling captivating stories with data. Unlike any other visualization
library, astetik is specifically made for day-to-day use by data
scientists and reduces learning curve compared to similar solutions
significantly.

"""

DISTNAME = 'astetik'
MAINTAINER = 'Mikko Kotila'
MAINTAINER_EMAIL = 'mailme@mikkokotila.com'
URL = 'http://mikkokotila.com'
LICENSE = 'MIT'
DOWNLOAD_URL = 'https://github.com/mikkokotila/pretty'
VERSION = '1.9.3'

try:
    from setuptools import setup
    _has_setuptools = True
except ImportError:
    from distutils.core import setup

def check_dependencies():
    install_requires = []

    try:
        import seaborn
    except ImportError:
        install_requires.append('seaborn')
    try:
        import numpy
    except ImportError:
        install_requires.append('numpy')
    #try:
    #    import matplotlib
    #except ImportError:
    #    install_requires.append('matplotlib')
    try:
        import pandas
    except ImportError:
        install_requires.append('pandas')
    try:
        import IPython
    except ImportError:
        install_requires.append('IPython')
    try:
        import statsmodels
    except ImportError:
        install_requires.append('statsmodels')
    try:
        import patsy
    except ImportError:
        install_requires.append('patsy')
    try:
        import geonamescache
    except ImportError:
        install_requires.append('geonamescache')


    return install_requires

if __name__ == "__main__":

    install_requires = check_dependencies()

    setup(name=DISTNAME,
        author=MAINTAINER,
        author_email=MAINTAINER_EMAIL,
        maintainer=MAINTAINER,
        maintainer_email=MAINTAINER_EMAIL,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        license=LICENSE,
        url=URL,
        version=VERSION,
        download_url=DOWNLOAD_URL,
        install_requires=install_requires,
        packages=['astetik',
                  'astetik.utils',
                  'astetik.tables',
                  'astetik.style',
                  'astetik.plots'],
        classifiers=[
                     'Intended Audience :: Science/Research',
                     'Programming Language :: Python :: 2.7',
                     'Programming Language :: Python :: 3.4',
                     'Programming Language :: Python :: 3.5',
                     'Programming Language :: Python :: 3.6',
                     'License :: OSI Approved :: MIT License',
                     'Topic :: Scientific/Engineering :: Visualization',
                     'Topic :: Multimedia :: Graphics',
                     'Operating System :: POSIX',
                     'Operating System :: Unix',
                     'Operating System :: MacOS'],
          )
