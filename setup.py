#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='kylin-system-tools',
    version='1.0.3',
    description='麒麟运维百宝箱',
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
    data_files=[
        ('share/kylin-system-tools/core', [
            'core/kylin_desktop_system_info.sh',
            'core/fix_printer.sh',
        ]),
        ('share/kylin-system-tools/tools/usb_fix_tool', [
            'tools/usb_fix_tool/usb_tool.py',
            'tools/usb_fix_tool/ui_assets.py',
            'tools/usb_fix_tool/ventoy-1.0.99-linux.tar.gz',
        ]),
        ('share/kylin-system-tools/tools/kylin_clean', [
            'tools/kylin_clean/clean_linux.py',
            'tools/kylin_clean/notify_clean_linux.py',
            'tools/kylin_clean/license_manager.py',
            'tools/kylin_clean/popup_warning.py',
            'tools/kylin_clean/ui_assets.py',
            'tools/kylin_clean/settings_ui.py',
            'tools/kylin_clean/settings_ui_qt.py',
            'tools/kylin_clean/kylin-cleanup.svg',
            'tools/kylin_clean/kylin-cleanup-settings.svg',
            'tools/kylin_clean/cleanup_user_data.sh',
            'tools/kylin_clean/service_toggle.sh',
        ]),
        ('share/kylin-system-tools/tools/kylin_clean/schedule', [
            'tools/kylin_clean/schedule/__init__.py',
            'tools/kylin_clean/schedule/py.typed',
        ]),
    ],
    classifiers=[
        'Operating System :: POSIX :: Linux',
        'Environment :: X11 Applications :: Qt',
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Systems Administration',
    ],
)
