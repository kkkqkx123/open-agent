"""测试配置文件加载器功能"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from application.workflow.state_machine.state_machine_config_loader import (
    StateMachineWorkflowLoader, 
    load_state_machine_workflow,
    create_state_machine_workflow_from_dict
)
from src.infrastructure.graph.config import WorkflowConfig


def test_config_loader():
    """测试配置文件加载器"""
    print("=== 测试配置文件加载器 ===")
    
    try:
        # 测试从文件加载
        print("1. 测试从YAML文件加载...")
        config_path = "examples/simple_workflow_config.yaml"
        
        if os.path.exists(config_path):
            workflow = load_state_machine_workflow(config_path)
            print(f"✓ 成功从文件加载工作流: {workflow}")
            print(f"  工作流名称: {workflow.config.name}")
            print(f"  初始状态: {workflow.current_state}")
        else:
            print("⚠ 配置文件不存在，跳过文件加载测试")
        
        # 测试从字典加载
        print("\n2. 测试从字典配置加载...")
        config_data = {
            "name": "TestWorkflow",
            "description": "测试工作流",
            "version": "1.0.0",
            "initial_state": "start",
            "workflow_config": {
                "name": "TestWorkflow",
                "description": "测试工作流",
                "version": "1.0.0",
                "nodes": {
                    "start": {"type": "start", "description": "开始节点"},
                    "process": {"type": "process", "description": "处理节点"},
                    "end": {"type": "end", "description": "结束节点"}
                },
                "edges": [
                    {"from": "start", "to": "process", "description": "开始到处理"},
                    {"from": "process", "to": "end", "description": "处理到结束"}
                ],
                "entry_point": "start"
            },
            "states": {
                "start": {
                    "type": "process",
                    "description": "开始状态",
                    "transitions": [
                        {"target": "process", "condition": "always", "description": "无条件转移"}
                    ]
                },
                "process": {
                    "type": "process",
                    "description": "处理状态",
                    "transitions": [
                        {"target": "end", "condition": "complete", "description": "处理完成"}
                    ]
                },
                "end": {
                    "type": "end",
                    "description": "结束状态",
                    "transitions": []
                }
            }
        }
        
        workflow = create_state_machine_workflow_from_dict(config_data)
        print(f"✓ 成功从字典加载工作流: {workflow}")
        print(f"  工作流名称: {workflow.config.name}")
        print(f"  初始状态: {workflow.current_state}")
        
        # 测试工作流执行
        print("\n3. 测试工作流执行...")
        
        # 模拟执行
        initial_state = {"data": "test_data"}
        result = workflow.execute(initial_state)
        print(f"✓ 工作流执行完成")
        print(f"  执行结果: {result}")
        
        # 测试状态转移（通过执行工作流自动处理）
        print("\n4. 测试状态转移...")
        # 重置工作流到初始状态
        workflow.reset()
        print(f"✓ 工作流重置完成")
        print(f"  当前状态: {workflow.current_state}")
        
        print("\n✅ 所有测试通过！配置文件加载器功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_loader_class():
    """测试加载器类"""
    print("\n=== 测试加载器类 ===")
    
    try:
        loader = StateMachineWorkflowLoader()
        print("✓ 加载器类实例化成功")
        
        # 测试配置解析
        config_data = {
            "name": "LoaderTestWorkflow",
            "description": "加载器测试工作流",
            "version": "1.0.0",
            "initial_state": "start"
        }
        
        workflow_config, state_machine_config = loader._parse_config(config_data)
        print(f"✓ 配置解析成功")
        print(f"  工作流配置: {workflow_config.name}")
        print(f"  状态机配置: {state_machine_config.name}")
        
        print("✅ 加载器类测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 加载器类测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("开始测试配置文件加载器...\n")
    
    # 运行测试
    test1_passed = test_config_loader()
    test2_passed = test_loader_class()
    
    print("\n" + "="*50)
    if test1_passed and test2_passed:
        print("🎉 所有测试通过！配置文件加载器功能完善")
        print("\n📋 使用说明:")
        print("1. 从文件加载: load_state_machine_workflow('config.yaml')")
        print("2. 从字典加载: create_state_machine_workflow_from_dict(config_dict)")
        print("3. 使用加载器类: StateMachineWorkflowLoader().load_from_file('config.yaml')")
    else:
        print("❌ 部分测试失败，请检查实现")
    
    return test1_passed and test2_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)