#!/usr/bin/env python3
"""接口集中化测试脚本

测试接口集中化后的架构是否能正常工作。
"""

import sys
import traceback

def test_consolidated_imports():
    """测试集中化后的接口导入"""
    print("🔍 测试集中化接口导入...")
    try:
        # 测试从新接口层直接导入
        from src.interfaces.workflow import (
            IWorkflow,
            IWorkflowExecutor,
            IWorkflowBuilder,
            IWorkflowTemplate,
            IWorkflowTemplateRegistry,
            IWorkflowVisualizer,
            IGraph,
            INode,
            IEdge,
            IGraphBuilder,
            INodeRegistry,
            IRoutingFunction,
            IRoutingRegistry
        )
        from src.interfaces.state.interfaces import IWorkflowState, IState
        
        print("✅ 新接口层直接导入成功")
        
        # 测试Core层重新导出
        from src.core.workflow import (
            IWorkflow as CoreIWorkflow,
            IWorkflowExecutor as CoreIWorkflowExecutor,
            IWorkflowBuilder as CoreIWorkflowBuilder,
            IWorkflowTemplate as CoreIWorkflowTemplate,
            IWorkflowTemplateRegistry as CoreIWorkflowTemplateRegistry,
            IWorkflowVisualizer as CoreIWorkflowVisualizer
        )
        from src.core.workflow.graph import (
            IGraph as CoreIGraph,
            INode as CoreINode,
            IEdge as CoreIEdge
        )
        
        print("✅ Core层重新导出成功")
        
        # 测试类型一致性
        assert IWorkflow == CoreIWorkflow, "工作流接口类型不一致"
        assert IWorkflowExecutor == CoreIWorkflowExecutor, "执行器接口类型不一致"
        assert IGraph == CoreIGraph, "图接口类型不一致"
        assert INode == CoreINode, "节点接口类型不一致"
        assert IEdge == CoreIEdge, "边接口类型不一致"
        
        print("✅ 接口类型一致性验证通过")
        
        return True
    except Exception as e:
        print(f"❌ 集中化接口导入失败: {e}")
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

def test_interface_completeness():
    """测试接口完整性"""
    print("\n🔍 测试接口完整性...")
    try:
        from src.interfaces.workflow import (
            IWorkflow,
            IWorkflowExecutor,
            IWorkflowBuilder,
            IWorkflowTemplate,
            IWorkflowTemplateRegistry,
            IWorkflowVisualizer,
            IGraph,
            INode,
            IEdge,
            IGraphBuilder,
            INodeRegistry,
            IRoutingFunction,
            IRoutingRegistry
        )
        
        # 检查接口是否可实例化（抽象类不应该能实例化）
        try:
            workflow = IWorkflow()
            print("❌ IWorkflow 不应该能直接实例化")
            return False
        except TypeError:
            print("✅ IWorkflow 正确地是抽象类")
        
        # 检查接口方法是否存在
        required_workflow_methods = ['workflow_id', 'name', 'add_node', 'add_edge', 'get_node', 'get_edge', 'validate']
        for method in required_workflow_methods:
            if not hasattr(IWorkflow, method):
                print(f"❌ IWorkflow 缺少方法: {method}")
                return False
        
        print("✅ 接口完整性验证通过")
        
        return True
    except Exception as e:
        print(f"❌ 接口完整性测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始接口集中化测试...\n")
    
    tests = [
        test_consolidated_imports,
        test_workflow_creation,
        test_services_layer,
        test_interface_completeness
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
        print("🎉 所有测试通过！接口集中化成功！")
        return 0
    else:
        print("⚠️ 部分测试失败，需要进一步修复")
        return 1

if __name__ == "__main__":
    sys.exit(main())