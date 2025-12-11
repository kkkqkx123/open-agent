#!/usr/bin/env python3
"""测试工作流配置系统

验证新的配置系统是否正常工作。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_workflow_config_mapper():
    """测试工作流配置映射器"""
    print("测试工作流配置映射器...")
    
    try:
        from src.core.workflow.mappers.config_mapper import get_workflow_config_mapper
        from src.core.workflow.graph_entities import Graph
        
        # 获取映射器
        mapper = get_workflow_config_mapper()
        print("✓ 成功获取工作流配置映射器")
        
        # 测试配置数据
        config_data = {
            "name": "test_workflow",
            "description": "测试工作流",
            "version": "1.0",
            "nodes": {
                "start": {
                    "name": "start",
                    "function_name": "start_function",
                    "description": "开始节点"
                },
                "end": {
                    "name": "end",
                    "function_name": "end_function",
                    "description": "结束节点"
                }
            },
            "edges": [
                {
                    "from": "start",
                    "to": "end",
                    "type": "simple"
                }
            ],
            "entry_point": "start"
        }
        
        # 测试配置验证
        validation_result = mapper.validate_config(config_data)
        if validation_result.is_valid:
            print("✓ 配置验证通过")
        else:
            print(f"✗ 配置验证失败: {validation_result.errors}")
            return False
        
        # 测试字典到实体转换
        graph = mapper.dict_to_entity(config_data)
        if isinstance(graph, Graph):
            print("✓ 字典到实体转换成功")
        else:
            print("✗ 字典到实体转换失败")
            return False
        
        # 测试实体到字典转换
        result_data = mapper.entity_to_dict(graph)
        if isinstance(result_data, dict) and "name" in result_data:
            print("✓ 实体到字典转换成功")
        else:
            print("✗ 实体到字典转换失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试工作流配置映射器失败: {e}")
        return False

def test_workflow_config_service():
    """测试工作流配置服务"""
    print("\n测试工作流配置服务...")
    
    try:
        from src.services.workflow.config_service import WorkflowConfigService
        from src.core.config.config_manager import UnifiedConfigManager
        from src.infrastructure.config.loader import ConfigLoader
        
        # 创建配置管理器
        config_loader = ConfigLoader()
        config_manager = UnifiedConfigManager(config_loader)
        print("✓ 成功创建配置管理器")
        
        # 创建工作流配置服务
        config_service = WorkflowConfigService(config_manager)
        print("✓ 成功创建工作流配置服务")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试工作流配置服务失败: {e}")
        return False

def test_config_interfaces():
    """测试配置接口"""
    print("\n测试配置接口...")
    
    try:
        from src.interfaces.config import (
            IConfigMapper,
            IModuleConfigService,
            IConfigManager,
            ValidationResult
        )
        print("✓ 成功导入配置接口")
        
        # 测试ValidationResult
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        if result.is_valid:
            print("✓ ValidationResult工作正常")
        else:
            print("✗ ValidationResult工作异常")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试配置接口失败: {e}")
        return False

def test_core_config_components():
    """测试核心配置组件"""
    print("\n测试核心配置组件...")
    
    try:
        from src.core.config.config_manager import (
            UnifiedConfigManager,
            ModuleConfigRegistry,
            ConfigMapperRegistry,
            CrossModuleResolver
        )
        print("✓ 成功导入核心配置组件")
        
        # 测试ModuleConfigRegistry
        registry = ModuleConfigRegistry()
        print("✓ 成功创建ModuleConfigRegistry")
        
        # 测试ConfigMapperRegistry
        mapper_registry = ConfigMapperRegistry()
        print("✓ 成功创建ConfigMapperRegistry")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试核心配置组件失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试工作流配置系统...")
    print("=" * 50)
    
    tests = [
        test_config_interfaces,
        test_core_config_components,
        test_workflow_config_mapper,
        test_workflow_config_service,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过，配置系统工作正常")
        return 0
    else:
        print("✗ 部分测试失败，需要检查配置系统")
        return 1

if __name__ == "__main__":
    sys.exit(main())