#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import json

class AuthService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def execute(self, cmd, input_data=None):
        """通过 pkexec 执行需要管理员权限的命令"""
        try:
            full_cmd = ['pkexec'] + cmd
            
            result = subprocess.run(
                full_cmd,
                input=input_data,
                capture_output=True,
                text=True
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
