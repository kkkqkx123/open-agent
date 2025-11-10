#!/usr/bin/env python3
"""
工作流配置验证测试脚本
用于快速测试验证器的各种功能
"""

import os
import sys
import yaml
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.validate_workflow_config import WorkflowConfigValidator


def test_validation_examples():
    """测试验证器的各种示例"""
    validator = WorkflowConfigValidator()
    
    # 测试用例1：完全无效的配置
    print("🧪 测试用例1：完全无效的配置")
    invalid_config = {
        "name": "invalid_workflow",
        # 缺少必要的 nodes, edges, entry_point
    }
    result = validator.validate_config(invalid_config)
    print(f"   有效: {result['valid']}")
    print(f"   错误数: {len(result['errors'])}")
    print(f"   警告数: {len(result['warnings'])}")
    print()
    
    # 测试用例2：包含死循环的配置
    print("🧪 测试用例2：包含死循环的配置")
    cycle_config = {
        "name": "cycle_workflow",
        "nodes": {
            "node_a": {"type": "llm_node", "config": {"llm_client": "mock"}},
            "node_b": {"type": "llm_node", "config": {"llm_client": "mock"}}
        },
        "edges": [
            {"from": "node_a", "to": "node_b", "type": "simple"},
            {"from": "node_b", "to": "node_a", "type": "simple"}  # 形成循环
        ],
        "entry_point": "node_a"
    }
    result = validator.validate_config(cycle_config)
    print(f"   有效: {result['valid']}")
    print(f"   错误数: {len(result['errors'])}")
    print(f"   警告数: {len(result['warnings'])}")
    if result['warnings']:
        for warning in result['warnings']:
            print(f"   ⚠️  {warning}")
    print()
    
    # 测试用例3：自调用配置
    print("🧪 测试用例3：自调用配置")
    self_call_config = {
        "name": "self_call_workflow", 
        "nodes": {
            "recursive_node": {"type": "llm_node", "config": {"llm_client": "mock"}}
        },
        "edges": [
            {"from": "recursive_node", "to": "recursive_node", "type": "simple"}  # 自调用
        ],
        "entry_point": "recursive_node"
    }
    result = validator.validate_config(self_call_config)
    print(f"   有效: {result['valid']}")
    print(f"   错误数: {len(result['errors'])}")
    print(f"   警告数: {len(result['warnings'])}")
    if result['warnings']:
        for warning in result['warnings']:
            print(f"   ⚠️  {warning}")
    print()
    
    # 测试用例4：内存风险配置
    print("🧪 测试用例4：内存风险配置")
    memory_risk_config = {
        "name": "memory_risk_workflow",
        "state_schema": {
            "name": "RiskyState",
            "fields": {
                "messages": {"type": "List[dict]", "default": []},  # 大类型
                "huge_data": {"type": "Dict[str, Any]", "default": {}}  # 大类型
            }
        },
        "nodes": {
            "start_node": {"type": "llm_node", "config": {"llm_client": "mock"}}
        },
        "edges": [],
        "entry_point": "start_node"
    }
    result = validator.validate_config(memory_risk_config)
    print(f"   有效: {result['valid']}")
    print(f"   错误数: {len(result['errors'])}")
    print(f"   警告数: {len(result['warnings'])}")
    if result['warnings']:
        for warning in result['warnings']:
            print(f"   ⚠️  {warning}")
    print()


def test_file_validation():
    """测试文件验证功能"""
    print("📁 测试文件验证功能")
    
    validator = WorkflowConfigValidator()
    
    # 测试存在的文件
    print("测试存在的反面教材文件:")
    result = validator.validate_file("configs/workflows/really_bad_workflow.yaml")
    print(f"   有效: {result['valid']}")
    print(f"   错误数: {len(result['errors'])}")
    print(f"   警告数: {len(result['warnings'])}")
    
    # 测试不存在的文件
    print("测试不存在的文件:")
    result = validator.validate_file("configs/workflows/nonexistent.yaml")
    print(f"   有效: {result['valid']}")
    print(f"   错误: {result['errors'][0] if result['errors'] else '无'}")
    print()


def main():
    """主函数"""
    print("🚀 工作流配置验证器测试")
    print("=" * 50)
    print()
    
    test_validation_examples()
    test_file_validation()
    
    print("=" * 50)
    print("✅ 测试完成！")


if __name__ == "__main__":
    main()