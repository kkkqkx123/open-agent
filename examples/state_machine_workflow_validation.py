"""状态机工作流验证示例

演示如何使用状态机工作流工厂从配置文件创建和执行工作流。
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.application.workflow.state_machine.state_machine_workflow_factory import (
    StateMachineWorkflowFactory, StateMachineConfigLoader, StateMachineWorkflow
)
from src.infrastructure.graph.config import WorkflowConfig
from src.infrastructure.graph.states import WorkflowState


def create_workflow_config(name: str, description: str) -> WorkflowConfig:
    """创建基本工作流配置"""
    return WorkflowConfig(
        name=name,
        description=description,
        version="1.0.0",
        nodes={},
        edges=[],
        entry_point="start"
    )


def test_deep_thinking_workflow():
    """测试深度思考工作流"""
    print("=== 测试深度思考工作流 ===")
    
    # 创建工厂
    factory = StateMachineWorkflowFactory()
    
    # 注册工作流类
    factory.register_workflow("deep_thinking", StateMachineWorkflow)
    
    # 创建工作流配置
    workflow_config = create_workflow_config("deep_thinking", "深度思考工作流测试")
    
    try:
        # 创建工作流实例
        workflow = factory.create_workflow(workflow_config)
        print(f"成功创建工作流: {workflow.__class__.__name__}")
        print(f"工作流名称: {workflow.state_machine_config.name}")
        print(f"初始状态: {workflow.state_machine_config.initial_state}")
        
        # 显示状态机配置信息
        print("\n状态机配置详情:")
        print(f"  名称: {workflow.state_machine_config.name}")
        print(f"  描述: {workflow.state_machine_config.description}")
        print(f"  版本: {workflow.state_machine_config.version}")
        print(f"  初始状态: {workflow.state_machine_config.initial_state}")
        print(f"  状态数量: {len(workflow.state_machine_config.states)}")
        
        # 显示所有状态
        print("\n状态列表:")
        for state_name, state_def in workflow.state_machine_config.states.items():
            print(f"  - {state_name} ({state_def.state_type.value}): {state_def.description}")
            if state_def.transitions:
                print(f"    转移:")
                for transition in state_def.transitions:
                    print(f"      -> {transition.target_state} ({transition.condition or '无条件'}): {transition.description}")
        
        # 验证配置
        errors = workflow.validate_config()
        if errors:
            print(f"\n配置验证错误:")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"\n配置验证通过")
            
        print("深度思考工作流测试完成\n")
        return True
        
    except Exception as e:
        print(f"创建或测试深度思考工作流失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ultra_thinking_workflow():
    """测试超思考工作流"""
    print("=== 测试超思考工作流 ===")
    
    # 创建工厂
    factory = StateMachineWorkflowFactory()
    
    # 注册工作流类
    factory.register_workflow("ultra_thinking", StateMachineWorkflow)
    
    # 创建工作流配置
    workflow_config = create_workflow_config("ultra_thinking", "超思考工作流测试")
    
    try:
        # 创建工作流实例
        workflow = factory.create_workflow(workflow_config)
        print(f"成功创建工作流: {workflow.__class__.__name__}")
        print(f"工作流名称: {workflow.state_machine_config.name}")
        print(f"初始状态: {workflow.state_machine_config.initial_state}")
        
        # 显示状态机配置信息
        print("\n状态机配置详情:")
        print(f"  名称: {workflow.state_machine_config.name}")
        print(f"  描述: {workflow.state_machine_config.description}")
        print(f"  版本: {workflow.state_machine_config.version}")
        print(f"  初始状态: {workflow.state_machine_config.initial_state}")
        print(f"  状态数量: {len(workflow.state_machine_config.states)}")
        
        # 显示所有状态
        print("\n状态列表:")
        for state_name, state_def in workflow.state_machine_config.states.items():
            print(f"  - {state_name} ({state_def.state_type.value}): {state_def.description}")
            if state_def.transitions:
                print(f"    转移:")
                for transition in state_def.transitions:
                    print(f"      -> {transition.target_state} ({transition.condition or '无条件'}): {transition.description}")
        
        # 验证配置
        errors = workflow.validate_config()
        if errors:
            print(f"\n配置验证错误:")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"\n配置验证通过")
            
        print("超思考工作流测试完成\n")
        return True
        
    except Exception as e:
        print(f"创建或测试超思考工作流失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_loading():
    """测试配置加载功能"""
    print("=== 测试配置加载功能 ===")
    
    try:
        # 测试加载深度思考工作流配置
        deep_thinking_config = StateMachineConfigLoader.load_from_yaml("configs/workflows/deep_thinking_workflow.yaml")
        print(f"成功加载深度思考工作流配置: {deep_thinking_config.name}")
        print(f"状态数量: {len(deep_thinking_config.states)}")
        
        # 验证配置
        errors = deep_thinking_config.validate()
        if errors:
            print(f"深度思考配置验证错误:")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"深度思考配置验证通过")
        
        # 测试加载超思考工作流配置
        ultra_thinking_config = StateMachineConfigLoader.load_from_yaml("configs/workflows/ultra_thinking_workflow.yaml")
        print(f"\n成功加载超思考工作流配置: {ultra_thinking_config.name}")
        print(f"状态数量: {len(ultra_thinking_config.states)}")
        
        # 验证配置
        errors = ultra_thinking_config.validate()
        if errors:
            print(f"超思考配置验证错误:")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"超思考配置验证通过")
            
        print("\n配置加载测试完成\n")
        return True
        
    except Exception as e:
        print(f"配置加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("状态机工作流验证示例")
    print("=" * 50)
    
    # 测试配置加载
    config_success = test_config_loading()
    
    # 测试深度思考工作流
    deep_thinking_success = test_deep_thinking_workflow()
    
    # 测试超思考工作流
    ultra_thinking_success = test_ultra_thinking_workflow()
    
    print("=" * 50)
    print("测试总结:")
    print(f"  配置加载测试: {'通过' if config_success else '失败'}")
    print(f"  深度思考工作流测试: {'通过' if deep_thinking_success else '失败'}")
    print(f"  超思考工作流测试: {'通过' if ultra_thinking_success else '失败'}")
    
    if config_success and deep_thinking_success and ultra_thinking_success:
        print("\n所有测试通过!")
        return 0
    else:
        print("\n部分测试失败!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)