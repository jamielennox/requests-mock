#!/usr/bin/env python

import os
import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

setup(
    name='requests-mock',
    version='0.1.0-dev',
    description='Mock out the requests package',
    author='Jamie Lennox',
    author_email='jamielennox@gmail.com',
    url='https://github.com/jamielennox/requests-mock',
    packages=[
        'requests_mock',
    ],
    package_dir={'requests_mock': 'requests_mock'},
    include_package_data=True,
    install_requires=[
        'requests',
        'fixtures',
    ],
    test_requires=[
        'testtools'
    ],
    license="BSD",
    zip_safe=False,
    keywords='requests mock',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License'
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
    test_suite='requests_mock.tests',
)
