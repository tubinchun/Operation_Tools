#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查文件换行符的脚本"""

import os
import sys
import io

# 确保输出编码为UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_file_line_endings(filepath):
    """检查文件的换行符类型"""
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        
        has_crlf = b'\r\n' in content
        has_lf = b'\n' in content and not has_crlf
        
        if has_crlf:
            return 'Windows (CRLF)'
        elif has_lf:
            return 'Linux (LF)'
        else:
            return 'Unknown'
    except Exception as e:
        return f'Error: {e}'

def main():
    base_dir = r'e:\Operation_Tools'
    
    # 要检查的文件列表
    check_patterns = [
        ('Python Scripts', '**/*.py'),
        ('Shell Scripts', '**/*.sh'),
        ('DEBIAN Files', 'debian/kylin-system-tools/DEBIAN/*'),
        ('Bin Scripts', 'debian/kylin-system-tools/usr/bin/*'),
        ('Desktop Files', 'debian/kylin-system-tools/usr/share/applications/*.desktop'),
        ('Service Files', '**/*.service'),
        ('Config Files', '**/*.json'),
    ]
    
    print("=" * 70)
    print("文件换行符检查报告")
    print("=" * 70)
    print()
    
    import glob
    
    all_stats = {'Windows (CRLF)': 0, 'Linux (LF)': 0, 'Unknown': 0, 'Error': 0}
    problem_files = []
    
    for category, pattern in check_patterns:
        print(f"\n{category}:")
        print("-" * 40)
        
        search_path = os.path.join(base_dir, pattern)
        files = glob.glob(search_path, recursive=True)
        
        if not files:
            print("  (无文件)")
            continue
        
        for filepath in files:
            if os.path.isfile(filepath):
                status = check_file_line_endings(filepath)
                if 'Error' in status:
                    all_stats['Error'] += 1
                else:
                    all_stats[status] += 1
                
                if status == 'Windows (CRLF)':
                    problem_files.append(filepath)
                
                # 只显示相对路径
                rel_path = os.path.relpath(filepath, base_dir)
                if status == 'Linux (LF)':
                    status_text = "[OK]"
                else:
                    status_text = "[!!"
                print(f"  {status_text} {rel_path}: {status}")
    
    print("\n" + "=" * 70)
    print("统计汇总")
    print("=" * 70)
    print(f"  Linux (LF)   : {all_stats['Linux (LF)']} 个文件")
    print(f"  Windows (CRLF): {all_stats['Windows (CRLF)']} 个文件")
    print(f"  Unknown       : {all_stats['Unknown']} 个文件")
    print(f"  Error         : {all_stats['Error']} 个文件")
    
    if problem_files:
        print("\n" + "=" * 70)
        print("需要修复的文件")
        print("=" * 70)
        for f in problem_files:
            print(f"  {os.path.relpath(f, base_dir)}")
    
    if all_stats['Windows (CRLF)'] == 0:
        print("\n[SUCCESS: 所有文件已正确转换为 Linux 格式！")
        return 0
    else:
        print(f"\n[FAIL]: 还有 {all_stats['Windows (CRLF)']} 个文件需要转换")
        return 1

if __name__ == '__main__':
    sys.exit(main())
