#!/usr/bin/env python3
"""架构重构测试脚本

测试重构后的架构是否能正常工作，特别是循环依赖问题是否已解决。
"""

import sys
import traceback

def test_basic_imports():
    """测试基本导入功能"""
    print("🔍 测试基本导入...")
    try:
        # 测试新的接口导入
        from src.interfaces.workflow.core import IWorkflow, ExecutionContext
        from src.interfaces.workflow.execution import IWorkflowExecutor
        from src.interfaces.workflow.graph import IGraph, INode, IEdge
        from src.interfaces.state.interfaces import IState, IWorkflowState
        
        print("✅ 新接口导入成功")
        
        # 测试Core层接口重新导出
        from src.core.workflow.interfaces import IWorkflow as CoreIWorkflow
        from src.core.workflow.graph.interfaces import INode as CoreINode
        
        print("✅ Core层接口重新导出成功")
        
        # 测试类型一致性
        assert IWorkflow == CoreIWorkflow, "工作流接口类型不一致"
        print("✅ 接口类型一致性验证通过")
        
        return True
    except Exception as e:
        print(f"❌ 基本导入失败: {e}")
        traceback.print_exc()
        return False

def test_workflow_creation():
    """测试工作流创建"""
    print("\n🔍 测试工作流创建...")
    try:
        from src.core.workflow.workflow import Workflow
        
        # 创建工作流实例
        workflow = Workflow("test-workflow", "Test Workflow")
        print(f"✅ 工作流创建成功: {workflow.name}")
        
        # 测试基本属性
        assert workflow.workflow_id == "test-workflow"
        assert workflow.name == "Test Workflow"
        print("✅ 工作流基本属性验证通过")
        
        return True
    except Exception as e:
        print(f"❌ 工作流创建失败: {e}")
        traceback.print_exc()
        return False

def test_workflow_instance():
    """测试工作流实例"""
    print("\n🔍 测试工作流实例...")
    try:
        from src.core.workflow.workflow_instance import WorkflowInstance
        
        # 创建简单配置
        config = {
            "workflow_id": "test-instance",
            "name": "Test Instance",
            "nodes": {},
            "edges": {}
        }
        
        # 创建工作流实例
        instance = WorkflowInstance(config)
        print(f"✅ 工作流实例创建成功: {instance.get_config().workflow_id}")
        
        return True
    except Exception as e:
        print(f"❌ 工作流实例创建失败: {e}")
        traceback.print_exc()
        return False

def test_services_layer():
    """测试Services层"""
    print("\n🔍 测试Services层...")
    try:
        from src.services.workflow.execution_service import WorkflowExecutionService
        from src.services.workflow.function_registry import FunctionRegistry
        
        # 创建服务实例
        execution_service = WorkflowExecutionService()
        function_registry = FunctionRegistry()
        
        print("✅ Services层组件创建成功")
        
        # 测试函数注册
        def test_function():
            return "test"
        
        function_registry.register("test", test_function, "node")
        retrieved = function_registry.get_node_function("test")
        
        assert retrieved == test_function, "函数注册/获取失败"
        print("✅ 函数注册表功能正常")
        
        return True
    except Exception as e:
        print(f"❌ Services层测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始架构重构测试...\n")
    
    tests = [
        test_basic_imports,
        test_workflow_creation,
        test_workflow_instance,
        test_services_layer
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n{'='*50}")
    print(f"📊 测试结果汇总:")
    print(f"通过: {passed}/{total} 个测试")
    
    if passed == total:
        print("🎉 所有测试通过！架构重构成功！")
        return 0
    else:
        print("⚠️ 部分测试失败，需要进一步修复")
        return 1

if __name__ == "__main__":
    sys.exit(main())