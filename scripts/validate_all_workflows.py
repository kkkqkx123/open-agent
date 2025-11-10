#!/usr/bin/env python3
"""
批量验证所有工作流配置文件的脚本
"""

import os
import sys
import yaml
import glob
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.validate_workflow_config import WorkflowConfigValidator


def find_all_workflow_files(base_path: str = "configs/workflows") -> List[str]:
    """查找所有工作流配置文件"""
    workflow_files = []
    
    # 查找主目录下的yaml文件
    main_pattern = os.path.join(base_path, "*.yaml")
    workflow_files.extend(glob.glob(main_pattern))
    
    # 查找examples子目录下的yaml文件
    examples_pattern = os.path.join(base_path, "examples", "*.yaml")
    workflow_files.extend(glob.glob(examples_pattern))
    
    return sorted(workflow_files)


def validate_workflow_file(file_path: str) -> Tuple[bool, List[str], List[str]]:
    """验证单个工作流文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        validator = WorkflowConfigValidator()
        result = validator.validate_config(config)
        return result["valid"], result["errors"], result["warnings"]
    except Exception as e:
        return False, [f"文件读取错误: {str(e)}"], []


def main():
    """主函数"""
    print("🔍 批量验证工作流配置文件")
    print("=" * 60)
    
    workflow_files = find_all_workflow_files()
    
    if not workflow_files:
        print("❌ 未找到任何工作流配置文件")
        return
    
    print(f"📁 找到 {len(workflow_files)} 个工作流配置文件")
    print()
    
    valid_count = 0
    warning_count = 0
    error_count = 0
    
    for i, file_path in enumerate(workflow_files, 1):
        rel_path = os.path.relpath(file_path)
        print(f"[{i:2d}/{len(workflow_files)}] 验证: {rel_path}")
        
        is_valid, errors, warnings = validate_workflow_file(file_path)
        
        if is_valid:
            print(f"    ✅ 有效")
            valid_count += 1
        else:
            print(f"    ❌ 无效")
            error_count += len(errors)
        
        if warnings:
            warning_count += len(warnings)
            for warning in warnings:
                print(f"    ⚠️  {warning}")
        
        if errors:
            for error in errors:
                print(f"    ❌ {error}")
        
        print()
    
    # 总结
    print("=" * 60)
    print("📊 验证总结:")
    print(f"   ✅ 有效配置: {valid_count}/{len(workflow_files)}")
    print(f"   ❌ 无效配置: {len(workflow_files) - valid_count}/{len(workflow_files)}")
    print(f"   ⚠️  总警告数: {warning_count}")
    print(f"   ❌ 总错误数: {error_count}")
    
    # 返回适当的退出码
    if error_count > 0:
        sys.exit(1)
    else:
        print("\n🎉 所有工作流配置验证通过！")
        sys.exit(0)


if __name__ == "__main__":
    main()