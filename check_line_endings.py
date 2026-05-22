#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查和修复文件换行符的脚本"""

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

def convert_to_lf(filepath):
    """将文件转换为LF换行符"""
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        
        content = content.replace(b'\r\n', b'\n')
        content = content.replace(b'\r', b'\n')
        
        with open(filepath, 'wb') as f:
            f.write(content)
        
        return True
    except Exception as e:
        return False

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    convert_mode = len(sys.argv) > 1 and sys.argv[1] == '--convert'
    
    check_patterns = [
        ('Python Scripts', '**/*.py'),
        ('Shell Scripts', '**/*.sh'),
        ('DEBIAN Files', 'debian/kylin-system-tools/DEBIAN/*'),
        ('Bin Scripts', 'debian/kylin-system-tools/usr/bin/*'),
        ('Desktop Files', 'debian/kylin-system-tools/usr/share/applications/*.desktop'),
        ('Service Files', '**/*.service'),
        ('Config Files', '**/*.json'),
        ('Core Files', 'core/**/*.py'),
        ('Client Files', 'client/**/*.py'),
        ('Server Files', 'server/**/*.py'),
        ('UI Files', 'ui/**/*.py'),
    ]
    
    if convert_mode:
        print("=" * 70)
        print("文件换行符转换工具 - LF格式转换模式")
        print("=" * 70)
    else:
        print("=" * 70)
        print("文件换行符检查报告")
        print("=" * 70)
    print()
    
    import glob
    
    all_stats = {'Windows (CRLF)': 0, 'Linux (LF)': 0, 'Unknown': 0, 'Error': 0, 'Converted': 0}
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
                
                if convert_mode and status == 'Windows (CRLF)':
                    if convert_to_lf(filepath):
                        status = 'Converted'
                        all_stats['Converted'] += 1
                    else:
                        status = 'Error'
                        all_stats['Error'] += 1
                else:
                    if 'Error' in status:
                        all_stats['Error'] += 1
                    else:
                        all_stats[status] += 1
                
                if status == 'Windows (CRLF)':
                    problem_files.append(filepath)
                
                rel_path = os.path.relpath(filepath, base_dir)
                if status == 'Linux (LF)':
                    status_text = "[OK]"
                elif status == 'Converted':
                    status_text = "[CONV]"
                else:
                    status_text = "[!!]"
                print(f"  {status_text} {rel_path}: {status}")
    
    print("\n" + "=" * 70)
    print("统计汇总")
    print("=" * 70)
    print(f"  Linux (LF)   : {all_stats['Linux (LF)']} 个文件")
    print(f"  Windows (CRLF): {all_stats['Windows (CRLF)']} 个文件")
    print(f"  Converted     : {all_stats['Converted']} 个文件")
    print(f"  Unknown       : {all_stats['Unknown']} 个文件")
    print(f"  Error         : {all_stats['Error']} 个文件")
    
    if all_stats['Windows (CRLF)'] == 0:
        print("\n[SUCCESS]: 所有文件已正确转换为 Linux 格式！")
        return 0
    else:
        print(f"\n[INFO]: 还有 {all_stats['Windows (CRLF)']} 个文件需要转换")
        if not convert_mode:
            print("        使用 --convert 参数运行脚本进行转换")
        return 1

if __name__ == '__main__':
    sys.exit(main())
