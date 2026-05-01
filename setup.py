#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='kylin-system-tools',
    version='1.0.0',
    description='银河麒麟运维管理工具',
    author='Kylin Team',
    packages=find_packages(),
    install_requires=[
        'PyQt5>=5.15.0',
    ],
    entry_points={
        'console_scripts': [
            'kylintools-server=server.__main__:main',
            'kylintools-client=client.__main__:main',
        ],
    },
    classifiers=[
        'Operating System :: POSIX :: Linux',
        'Environment :: X11 Applications :: Qt',
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Systems Administration',
    ],
)
