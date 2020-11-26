# To use a consistent encoding
from codecs import open
from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='cw2',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.3.0-beta',

    description='A reengineered framework to run experiments on an computing cluster.',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/ALRhub/cw2',

    # Author details
    author='Maixmilian Li',
    author_email='maixmilian.xiling.li@gmail.com',

    # Choose your license
    # license='BSD-3',

    classifiers=[
        # How mature is this project?
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Beta',

        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Topic :: System :: Distributed Computing',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Education',

        #'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Environment :: Console'
    ],

    python_requires='>=3',

    # What does your project relate to?
    keywords=['scientific', 'experiments',
              'distributed computing', 'mpi', 'research'],

    packages=['cw2', 'cw2.cw_data'],
    package_data={'cw2': ['default_sbatch.sh']},

    install_requires=['PyYAML', 'numpy', 'pandas', 'attrdict', 'joblib'],
)
