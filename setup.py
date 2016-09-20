#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name='havoc',
        version='0.1.0',
        description='HAvOC (HAproxy clOud Configuration)',
        author='TubeMogul Inc.',
        install_requires=[
            'python-daemon',
            'jinja2',
            'click',
            'boto',
            'python-novaclient',
            'PyYAML'
        ],
        packages=find_packages(),
        package_dir={'havoc': 'havoc'},
        scripts=['bin/havoc']
        )
