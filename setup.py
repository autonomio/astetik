#! /usr/bin/env python
#
import os
# temporarily redirect config directory to prevent matplotlib importing
# testing that for writeable directory which results in sandbox error in
# certain easy_install versions
os.environ["MPLCONFIGDIR"] = "."

DESCRIPTION = "Somecode Twitter Science and Research Platform"
LONG_DESCRIPTION = """\

SOMECODE is a research platform for serious observation and analysis 
of Twitter data. SOMECODE brings together 9 years of unbroken continuity 
in developing social media research tools. Previous tools and processes 
developed by the contributor team are in daily use by many FORTUNE100 
companies and major advertising agencies. SOMECODE is the solution we 
always wanted to build, but due to the kinds of restraints commercial 
entities have, never got to.

"""

DISTNAME = 'somecode'
MAINTAINER = 'Mikko Kotila'
MAINTAINER_EMAIL = 'mailme@mikkokotila.com'
URL = 'http://botlab.io'
LICENSE = 'MIT'
DOWNLOAD_URL = 'https://github.com/S0MEC0DE/'
VERSION = '1.0.1'

try:
    from setuptools import setup
    _has_setuptools = True
except ImportError:
    from distutils.core import setup

def check_dependencies():
    install_requires = []

    # Just make sure dependencies exist, I haven't rigorously
    # tested what the minimal versions that will work are
    # (help on that would be awesome)
    try:
        import numpy
    except ImportError:
        install_requires.append('numpy')
    try:
        import seaborn
    except ImportError:
        install_requires.append('seaborn')
    try:
        import matplotlib
    except ImportError:
        install_requires.append('matplotlib')
    try:
        import pandas
    except ImportError:
        install_requires.append('pandas')
    try:
        import nltk
    except ImportError:
        install_requires.append('nltk')
    try:
        import tweepy
    except ImportError:
        install_requires.append('tweepy')
    try:
        import twython
    except ImportError:
        install_requires.append('twython')
    try:
        import IPython
    except ImportError:
        install_requires.append('IPython')

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
        packages=['somecode'],
        classifiers=[
                     'Intended Audience :: Science/Research',
                     'Programming Language :: Python :: 2.7',
                     'Operating System :: POSIX',
                     'Operating System :: Unix',
                     'Operating System :: MacOS'],
          )
