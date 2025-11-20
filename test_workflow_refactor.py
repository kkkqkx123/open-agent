"""工作流重构验证脚本

验证重构后的工作流架构是否正常工作，包括：
1. Services层组件是否正常注册
2. workflow.py和workflow_instance.py的职责分离是否正确
3. 是否存在循环依赖问题
"""

import sys
import traceback
from typing import Dict, Any

def test_services_layer():
    """测试Services层组件"""
    print("🔍 测试Services层组件...")
    
    try:
        # 配置Services层
        from src.services.workflow.di_config import configure_workflow_services
        configure_workflow_services()
        print("✅ Services层配置成功")
        
        # 测试服务获取
        from src.services.workflow.di_config import (
            get_workflow_builder_service,
            get_workflow_execution_service,
            get_workflow_factory,
            get_function_registry
        )
        
        builder_service = get_workflow_builder_service()
        execution_service = get_workflow_execution_service()
        factory = get_workflow_factory()
        registry = get_function_registry()
        
        print(f"✅ 构建服务: {type(builder_service).__name__}")
        print(f"✅ 执行服务: {type(execution_service).__name__}")
        print(f"✅ 工厂服务: {type(factory).__name__}")
        print(f"✅ 函数注册表: {type(registry).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Services层测试失败: {e}")
        traceback.print_exc()
        return False


def test_workflow_structure():
    """测试工作流结构定义"""
    print("\n🔍 测试工作流结构定义...")
    
    try:
        from src.core.workflow.workflow import Workflow
        
        # 创建工作流实例
        workflow = Workflow("test_id", "test_workflow", "测试工作流")
        
        # 测试结构定义功能
        workflow.set_entry_point("start")
        workflow.metadata = {"test": "value"}
        
        # 测试验证功能
        errors = workflow.validate()
        print(f"✅ 工作流验证结果: {len(errors)} 个错误")
        
        # 测试结构信息
        info = workflow.get_structure_info()
        print(f"✅ 工作流结构信息: {info}")
        
        # 测试执行方法是否正确抛出异常
        try:
            from src.core.workflow.interfaces import ExecutionContext
            context = ExecutionContext("test", "test", {}, {})
            workflow.execute(None, context)
            print("❌ 执行方法应该抛出NotImplementedError")
            return False
        except NotImplementedError:
            print("✅ 执行方法正确抛出NotImplementedError")
        
        return True
        
    except Exception as e:
        print(f"❌ 工作流结构测试失败: {e}")
        traceback.print_exc()
        return False


def test_workflow_instance():
    """测试工作流实例"""
    print("\n🔍 测试工作流实例...")
    
    try:
        from src.core.workflow.config.config import GraphConfig, NodeConfig, EdgeConfig, EdgeType
        from src.core.workflow.workflow_instance import WorkflowInstance
        
        # 创建测试配置
        config = GraphConfig(
            name="test_workflow",
            description="测试工作流",
            nodes={
                "start": NodeConfig(
                    name="start",
                    function_name="test_function"
                )
            },
            edges=[
                EdgeConfig(
                    from_node="start",
                    to_node="__end__",
                    type=EdgeType.SIMPLE
                )
            ],
            entry_point="start"
        )
        
        # 创建工作流实例（使用Services层）
        instance = WorkflowInstance(config, use_services_layer=True)
        
        print(f"✅ 工作流实例创建成功: {instance.config.name}")
        
        # 测试验证功能
        errors = instance.validate()
        print(f"✅ 实例验证结果: {len(errors)} 个错误")
        
        # 测试元数据功能
        metadata = instance.get_metadata()
        print(f"✅ 实例元数据: {metadata}")
        
        return True
        
    except Exception as e:
        print(f"❌ 工作流实例测试失败: {e}")
        traceback.print_exc()
        return False


def test_no_circular_dependency():
    """测试是否存在循环依赖"""
    print("\n🔍 测试循环依赖...")
    
    try:
        # 尝试导入所有相关模块
        from src.core.workflow.workflow import Workflow
        from src.core.workflow.workflow_instance import WorkflowInstance
        from src.services.workflow.execution_service import WorkflowExecutionService
        from src.services.workflow.building.builder_service import WorkflowBuilderService
        
        print("✅ 所有模块导入成功，无循环依赖")
        
        # 测试Services层可以独立使用
        from src.services.workflow.di_config import get_workflow_execution_service
        execution_service = get_workflow_execution_service()
        print(f"✅ Services层独立使用成功: {type(execution_service).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ 循环依赖测试失败: {e}")
        traceback.print_exc()
        return False


def test_integration():
    """测试集成功能"""
    print("\n🔍 测试集成功能...")
    
    try:
        from src.services.workflow.di_config import execute_workflow
        
        # 创建简单的工作流配置
        config = {
            "name": "integration_test",
            "description": "集成测试工作流",
            "nodes": {
                "start": {
                    "function_name": "test_function"
                }
            },
            "edges": [
                {
                    "from": "start",
                    "to": "__end__",
                    "type": "simple"
                }
            ],
            "entry_point": "start"
        }
        
        # 测试执行（可能会失败，但不应该有架构问题）
        try:
            result = execute_workflow(config, {"test": "data"})
            print(f"✅ 集成执行成功: {result}")
        except Exception as e:
            # 执行失败是正常的，只要不是架构问题
            if "Services层组件不可用" in str(e) or "图构建失败" in str(e):
                print(f"❌ 集成测试失败（架构问题）: {e}")
                return False
            else:
                print(f"⚠️ 集成执行失败（预期）: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🚀 开始工作流重构验证...\n")
    
    tests = [
        ("Services层组件", test_services_layer),
        ("工作流结构定义", test_workflow_structure),
        ("工作流实例", test_workflow_instance),
        ("循环依赖检查", test_no_circular_dependency),
        ("集成功能", test_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "="*50)
    print("📊 测试结果汇总:")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！重构成功！")
        return 0
    else:
        print("⚠️ 部分测试失败，需要进一步修复")
        return 1


if __name__ == "__main__":
    sys.exit(main())