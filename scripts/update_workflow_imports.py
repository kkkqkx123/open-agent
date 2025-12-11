#!/usr/bin/env python3
"""
批量更新工作流导入路径脚本

将所有从 src.core.workflow.config.config 导入的类
改为从 src.core.workflow.graph_entities 导入
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# 定义导入映射
IMPORT_MAPPINGS = {
    'from src.core.workflow.config.config import': 'from src.core.workflow.graph_entities import',
    'from src.core.workflow.config.config import GraphConfig': 'from src.core.workflow.graph_entities import GraphConfig',
    'from src.core.workflow.config.config import NodeConfig': 'from src.core.workflow.graph_entities import NodeConfig',
    'from src.core.workflow.config.config import EdgeConfig': 'from src.core.workflow.graph_entities import EdgeConfig',
    'from src.core.workflow.config.config import StateFieldConfig': 'from src.core.workflow.graph_entities import StateFieldConfig',
    'from src.core.workflow.config.config import GraphStateConfig': 'from src.core.workflow.graph_entities import GraphStateConfig',
    'from src.core.workflow.config.config import WorkflowConfig': 'from src.core.workflow.graph_entities import WorkflowConfig',
    'from src.core.workflow.config.config import EdgeType': 'from src.core.workflow.graph_entities import EdgeType',
}

# 需要更新的文件模式
FILE_PATTERNS = [
    r'.*\.py$',  # 所有Python文件
]

# 排除的目录
EXCLUDE_DIRS = {
    '__pycache__',
    '.git',
    '.pytest_cache',
    '.venv',
    'venv',
    'node_modules',
    'dist',
    'build',
}

def should_process_file(file_path: Path) -> bool:
    """判断是否应该处理该文件"""
    # 检查文件扩展名
    if not file_path.suffix == '.py':
        return False
    
    # 检查是否在排除目录中
    for part in file_path.parts:
        if part in EXCLUDE_DIRS:
            return False
    
    return True

def update_file_imports(file_path: Path) -> Tuple[int, List[str]]:
    """更新文件中的导入路径"""
    changes_count = 0
    changes_made = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 应用导入映射
        for old_import, new_import in IMPORT_MAPPINGS.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                changes_count += 1
                changes_made.append(f"  {old_import} -> {new_import}")
        
        # 如果有更改，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 更新文件: {file_path}")
            for change in changes_made:
                print(change)
        else:
            print(f"- 无需更新: {file_path}")
            
    except Exception as e:
        print(f"✗ 处理文件失败 {file_path}: {e}")
        return 0, []
    
    return changes_count, changes_made

def find_python_files(root_dir: Path) -> List[Path]:
    """查找所有Python文件"""
    python_files = []
    
    for file_path in root_dir.rglob('*.py'):
        if should_process_file(file_path):
            python_files.append(file_path)
    
    return sorted(python_files)

def main():
    """主函数"""
    print("开始批量更新工作流导入路径...")
    print("=" * 60)
    
    # 获取项目根目录
    root_dir = Path(__file__).parent.parent
    src_dir = root_dir / 'src'
    
    if not src_dir.exists():
        print(f"错误: 找不到src目录: {src_dir}")
        return
    
    # 查找所有Python文件
    python_files = find_python_files(src_dir)
    print(f"找到 {len(python_files)} 个Python文件")
    print()
    
    # 统计信息
    total_files = 0
    updated_files = 0
    total_changes = 0
    
    # 处理每个文件
    for file_path in python_files:
        total_files += 1
        changes_count, _ = update_file_imports(file_path)
        if changes_count > 0:
            updated_files += 1
            total_changes += changes_count
        print()
    
    # 输出统计信息
    print("=" * 60)
    print("更新完成!")
    print(f"总文件数: {total_files}")
    print(f"更新文件数: {updated_files}")
    print(f"总更改数: {total_changes}")
    
    if updated_files > 0:
        print("\n建议运行以下命令验证更改:")
        print("  uv run mypy src/")
        print("  uv run pytest tests/")

if __name__ == '__main__':
    main()