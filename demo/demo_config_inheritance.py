#!/usr/bin/env python3
"""
配置继承功能演示脚本

演示如何使用新的配置继承系统来加载和验证配置文件。
"""

import asyncio
import logging
from pathlib import Path

from src.infrastructure import (
    FileConfigLoader, 
    InheritanceConfigLoader,
    ConfigInheritanceHandler,
    WorkflowConfigModel,
    ConfigType,
    validate_config_with_model
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_basic_inheritance():
    """演示基础配置继承功能"""
    print("=" * 60)
    print("演示1: 基础配置继承功能")
    print("=" * 60)
    
    # 创建配置加载器（启用继承）
    config_loader = FileConfigLoader(enable_inheritance=True)
    
    try:
        # 加载ReAct工作流配置（继承自base_workflow.yaml）
        config = config_loader.load("workflows/react_workflow.yaml")
        
        print("成功加载ReAct工作流配置！")
        print(f"配置名称: {config.get('metadata', {}).get('name', 'Unknown')}")
        print(f"配置版本: {config.get('metadata', {}).get('version', 'Unknown')}")
        print(f"工作流名称: {config.get('workflow_name', 'Unknown')}")
        print(f"最大迭代次数: {config.get('max_iterations', 'Unknown')}")
        print(f"节点数量: {len(config.get('nodes', {}))}")
        print(f"边数量: {len(config.get('edges', []))}")
        
        # 显示继承信息
        if 'inherits_from' in config:
            print(f"继承自: {config['inherits_from']}")
        
        # 显示状态模式
        state_schema = config.get('state_schema', {})
        if state_schema:
            print(f"状态模式名称: {state_schema.get('name', 'Unknown')}")
            print(f"状态字段数量: {len(state_schema.get('fields', {}))}")
        
        return config
        
    except Exception as e:
        print(f"加载配置失败: {e}")
        return None


def demo_config_validation():
    """演示配置验证功能"""
    print("\n" + "=" * 60)
    print("演示2: 配置验证功能")
    print("=" * 60)
    
    config_loader = FileConfigLoader(enable_inheritance=True)
    
    try:
        # 加载配置
        config_dict = config_loader.load("workflows/react_workflow.yaml")
        
        # 使用Pydantic模型验证配置
        errors = validate_config_with_model(config_dict, ConfigType.WORKFLOW)
        
        if errors:
            print("配置验证失败:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("配置验证通过！")
            
            # 创建配置模型实例
            try:
                model = WorkflowConfigModel(**config_dict)
                print(f"配置模型创建成功: {model.metadata.name}")
                print(f"验证规则数量: {len(model.validation_rules)}")
                
                # 执行自定义验证
                custom_errors = model.validate_config()
                if custom_errors:
                    print("自定义验证错误:")
                    for error in custom_errors:
                        print(f"  - {error}")
                else:
                    print("自定义验证通过！")
                    
            except Exception as e:
                print(f"创建配置模型失败: {e}")
        
    except Exception as e:
        print(f"配置验证过程失败: {e}")


def demo_inheritance_handler():
    """演示配置继承处理器"""
    print("\n" + "=" * 60)
    print("演示3: 配置继承处理器")
    print("=" * 60)
    
    handler = ConfigInheritanceHandler()
    
    # 创建一个测试配置
    test_config = {
        "inherits_from": "base_workflow.yaml",
        "metadata": {
            "name": "test_workflow",
            "version": "2.0.0",
            "description": "测试工作流"
        },
        "workflow_name": "test_workflow",
        "max_iterations": 15,
        "additional_field": "额外字段"
    }
    
    try:
        # 解析继承关系
        resolved_config = handler.resolve_inheritance(test_config, Path("configs/workflows"))
        
        print("继承解析成功！")
        print(f"最终配置名称: {resolved_config.get('metadata', {}).get('name', 'Unknown')}")
        print(f"最终版本: {resolved_config.get('metadata', {}).get('version', 'Unknown')}")
        print(f"最大迭代次数: {resolved_config.get('max_iterations', 'Unknown')}")
        print(f"额外字段: {resolved_config.get('additional_field', 'Unknown')}")
        
        # 显示合并的字段
        if 'nodes' in resolved_config:
            print(f"继承的节点数量: {len(resolved_config['nodes'])}")
        if 'edges' in resolved_config:
            print(f"继承的边数量: {len(resolved_config['edges'])}")
        
        return resolved_config
        
    except Exception as e:
        print(f"继承解析失败: {e}")
        return None


def demo_config_comparison():
    """演示配置对比功能"""
    print("\n" + "=" * 60)
    print("演示4: 配置对比功能")
    print("=" * 60)
    
    config_loader = FileConfigLoader(enable_inheritance=True)
    
    try:
        # 加载基础配置
        base_config = config_loader.load("workflows/base_workflow.yaml")
        
        # 加载继承配置
        react_config = config_loader.load("workflows/react_workflow.yaml")
        
        print("基础工作流 vs ReAct工作流对比:")
        print(f"基础配置节点: {len(base_config.get('nodes', {}))}")
        print(f"ReAct配置节点: {len(react_config.get('nodes', {}))}")
        print(f"基础配置边: {len(base_config.get('edges', []))}")
        print(f"ReAct配置边: {len(react_config.get('edges', []))}")
        print(f"基础配置最大迭代: {base_config.get('max_iterations', 'Unknown')}")
        print(f"ReAct配置最大迭代: {react_config.get('max_iterations', 'Unknown')}")
        print(f"基础配置超时: {base_config.get('timeout', 'Unknown')}")
        print(f"ReAct配置超时: {react_config.get('timeout', 'Unknown')}")
        
        # 显示状态模式差异
        base_schema = base_config.get('state_schema', {})
        react_schema = react_config.get('state_schema', {})
        
        print(f"基础状态字段: {len(base_schema.get('fields', {}))}")
        print(f"ReAct状态字段: {len(react_schema.get('fields', {}))}")
        
    except Exception as e:
        print(f"配置对比失败: {e}")


async def demo_async_config_loading():
    """演示异步配置加载（模拟）"""
    print("\n" + "=" * 60)
    print("演示5: 异步配置加载")
    print("=" * 60)
    
    # 模拟异步配置加载
    async def load_config_async(config_path: str):
        """异步加载配置"""
        await asyncio.sleep(0.1)  # 模拟异步操作
        config_loader = FileConfigLoader(enable_inheritance=True)
        return config_loader.load(config_path)
    
    try:
        # 并发加载多个配置
        tasks = [
            load_config_async("workflows/base_workflow.yaml"),
            load_config_async("workflows/react_workflow.yaml")
        ]
        
        configs = await asyncio.gather(*tasks)
        
        print("异步配置加载完成！")
        for i, config in enumerate(configs):
            if config:
                print(f"配置 {i+1}: {config.get('metadata', {}).get('name', 'Unknown')}")
        
    except Exception as e:
        print(f"异步配置加载失败: {e}")


def main():
    """主函数"""
    print("配置继承系统演示")
    print("=" * 60)
    
    # 演示1: 基础配置继承
    demo_basic_inheritance()
    
    # 演示2: 配置验证
    demo_config_validation()
    
    # 演示3: 配置继承处理器
    demo_inheritance_handler()
    
    # 演示4: 配置对比
    demo_config_comparison()
    
    # 演示5: 异步配置加载
    asyncio.run(demo_async_config_loading())
    
    print("\n" + "=" * 60)
    print("所有演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()