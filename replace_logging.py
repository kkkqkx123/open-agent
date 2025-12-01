#!/usr/bin/env python3
"""批量替换logging导入的脚本"""

import os
import re
from pathlib import Path

def replace_logging_in_file(file_path: Path) -> bool:
    """替换单个文件中的logging导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 替换导入语句
        content = re.sub(
            r'import logging',
            'from src.services.logger import get_logger',
            content
        )
        
        # 替换logger初始化
        content = re.sub(
            r'logger = logging\.getLogger\(__name__\)',
            'logger = get_logger(__name__)',
            content
        )
        
        # 替换其他logging.getLogger调用
        content = re.sub(
            r'logging\.getLogger\(([^)]+)\)',
            r'get_logger(\1)',
            content
        )
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"已更新: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return False

def replace_logging_in_directory(directory: Path) -> int:
    """递归替换目录中的所有Python文件"""
    count = 0
    
    for file_path in directory.rglob('*.py'):
        if replace_logging_in_file(file_path):
            count += 1
    
    return count

if __name__ == '__main__':
    # 替换核心模块
    core_dir = Path('src/core')
    if core_dir.exists():
        count = replace_logging_in_directory(core_dir)
        print(f"核心模块: 已更新 {count} 个文件")
    
    # 替换服务层
    services_dir = Path('src/services')
    if services_dir.exists():
        count = replace_logging_in_directory(services_dir)
        print(f"服务层: 已更新 {count} 个文件")
    
    # 替换适配器层
    adapters_dir = Path('src/adapters')
    if adapters_dir.exists():
        count = replace_logging_in_directory(adapters_dir)
        print(f"适配器层: 已更新 {count} 个文件")