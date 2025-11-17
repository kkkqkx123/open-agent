#!/usr/bin/env python3
"""
批量更新导入路径脚本

用于将旧架构的导入路径更新为新的扁平化架构路径。
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# 导入路径映射表
IMPORT_MAPPINGS = {
    # Tools 相关导入路径
    "from src.domain.tools.": "from src.core.tools.",
    "from src.infrastructure.tools.": "from src.core.tools.",
    "import src.domain.tools.": "import src.core.tools.",
    "import src.infrastructure.tools.": "import src.core.tools.",
    
    # LLM 相关导入路径
    "from src.infrastructure.llm.": "from src.core.llm.",
    "import src.infrastructure.llm.": "import src.core.llm.",
    
    # 具体模块映射
    "src.domain.tools.interfaces": "src.core.tools.interfaces",
    "src.domain.tools.entities": "src.core.tools.entities",
    "src.infrastructure.tools.factory": "src.core.tools.factory",
    "src.infrastructure.tools.loaders": "src.core.tools.loaders",
    "src.infrastructure.tools.formatter": "src.core.tools.formatter",
    "src.infrastructure.llm.interfaces": "src.core.llm.interfaces",
    "src.infrastructure.llm.entities": "src.core.llm.entities",
    "src.infrastructure.llm.factory": "src.core.llm.factory",
    "src.infrastructure.llm.providers": "src.core.llm.providers",
    "src.infrastructure.llm.clients": "src.core.llm.clients",
    
    # 工具类型映射
    "BuiltinTool": "NativeTool",
    "NativeTool": "RestTool",  # 注意：这是旧NativeTool到新RestTool的映射
    "builtin_tool": "native_tool",
    "native_tool": "rest_tool",
    "BuiltinToolConfig": "NativeToolConfig",
    "NativeToolConfig": "RestToolConfig",
    "builtin": "native",
    "native": "rest",
}

# 需要排除的目录和文件
EXCLUDE_DIRS = {
    ".git", ".pytest_cache", ".venv", "__pycache__", ".idea", ".vscode",
    "node_modules", "dist", "build"
}

EXCLUDE_FILES = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bat", ".sh",
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".lock",
    "update_import_paths.py"  # 排除脚本本身
}

def should_process_file(file_path: Path) -> bool:
    """判断文件是否需要处理"""
    if file_path.suffix != ".py":
        return False
    
    # 检查文件名是否在排除列表中
    if any(file_path.name.endswith(ext) for ext in EXCLUDE_FILES):
        return False
    
    # 检查路径中是否包含排除的目录
    for part in file_path.parts:
        if part in EXCLUDE_DIRS:
            return False
    
    return True

def update_imports_in_file(file_path: Path) -> Tuple[int, List[str]]:
    """更新单个文件中的导入路径"""
    changes_count = 0
    changes_made = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            original_content = content
        
        # 应用导入路径映射
        for old_path, new_path in IMPORT_MAPPINGS.items():
            if old_path in content:
                content = content.replace(old_path, new_path)
                changes_count += content.count(old_path)
                changes_made.append(f"{old_path} -> {new_path}")
        
        # 如果有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return 0, []
    
    return changes_count, changes_made

def find_python_files(root_dir: Path) -> List[Path]:
    """查找所有需要处理的Python文件"""
    python_files = []
    
    for file_path in root_dir.rglob("*.py"):
        if should_process_file(file_path):
            python_files.append(file_path)
    
    return python_files

def main():
    """主函数"""
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print(f"项目根目录: {project_root}")
    print(f"开始更新导入路径...")
    
    # 查找所有Python文件
    python_files = find_python_files(project_root)
    print(f"找到 {len(python_files)} 个Python文件需要检查")
    
    total_changes = 0
    processed_files = 0
    
    # 处理每个文件
    for file_path in python_files:
        changes_count, changes_made = update_imports_in_file(file_path)
        
        if changes_count > 0:
            processed_files += 1
            total_changes += changes_count
            print(f"\n文件: {file_path.relative_to(project_root)}")
            print(f"  修改数量: {changes_count}")
            for change in changes_made:
                print(f"    {change}")
    
    print(f"\n更新完成!")
    print(f"处理文件数: {processed_files}")
    print(f"总修改数: {total_changes}")
    
    if total_changes == 0:
        print("没有找到需要更新的导入路径。")
        return 0
    else:
        print("导入路径更新成功!")
        return 1

if __name__ == "__main__":
    sys.exit(main())