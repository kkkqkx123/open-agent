"""状态机工作流测试脚本

测试基于状态机的工作流基类的功能。
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.application.workflow.state_machine_workflow import (
    StateMachineWorkflow, StateMachineConfig, StateDefinition, Transition, StateType
)
from src.application.workflow.state_machine_workflow_factory import (
    StateMachineWorkflowFactory, register_state_machine_workflow, create_state_machine_workflow
)
from src.infrastructure.graph.config import WorkflowConfig


def test_state_machine_config():
    """测试状态机配置"""
    print("=== 测试状态机配置 ===")
    
    # 创建配置
    config = StateMachineConfig(
        name="test_workflow",
        description="测试工作流",
        version="1.0.0",
        initial_state="start"
    )
    
    # 添加状态
    start_state = StateDefinition("start", StateType.START, description="开始状态")
    process_state = StateDefinition("process", StateType.PROCESS, description="处理状态")
    end_state = StateDefinition("end", StateType.END, description="结束状态")
    
    config.add_state(start_state)
    config.add_state(process_state)
    config.add_state(end_state)
    
    # 添加转移
    start_state.add_transition(Transition("process"))
    process_state.add_transition(Transition("end"))
    
    # 验证配置
    errors = config.validate()
    if errors:
        print(f"配置验证失败: {errors}")
        return False
    else:
        print("配置验证成功")
    
    # 测试状态获取
    assert config.get_state("start") is not None
    assert config.get_state("process") is not None
    assert config.get_state("end") is not None
    assert config.get_state("nonexistent") is None
    print("状态获取测试通过")
    
    # 测试可达性
    reachable_states = config._get_reachable_states()
    assert "start" in reachable_states
    assert "process" in reachable_states
    assert "end" in reachable_states
    print("可达性测试通过")
    
    return True


def test_state_machine_workflow():
    """测试状态机工作流"""
    print("\n=== 测试状态机工作流 ===")
    
    # 创建状态机配置
    state_machine_config = StateMachineConfig(
        name="test_workflow",
        description="测试工作流",
        version="1.0.0",
        initial_state="start"
    )
    
    # 定义状态
    start_state = StateDefinition("start", StateType.START, description="开始状态")
    process_state = StateDefinition("process", StateType.PROCESS, description="处理状态")
    end_state = StateDefinition("end", StateType.END, description="结束状态")
    
    state_machine_config.add_state(start_state)
    state_machine_config.add_state(process_state)
    state_machine_config.add_state(end_state)
    
    # 定义转移
    start_state.add_transition(Transition("process"))
    process_state.add_transition(Transition("end"))
    
    # 创建工作流配置
    workflow_config = WorkflowConfig(
        name="test_workflow",
        description="测试工作流",
        version="1.0.0",
        nodes={},  # 空节点配置
        edges=[],  # 空边配置
        entry_point="start"
    )
    
    # 创建测试工作流类
    class TestStateMachineWorkflow(StateMachineWorkflow):
        def handle_process(self, state, config):
            """处理状态处理函数"""
            state["processed"] = True
            state["process_config"] = config
            return state
        
        def handle_start(self, state, config):
            """开始状态处理函数"""
            state["started"] = True
            return state
    
    # 创建工作流实例
    workflow = TestStateMachineWorkflow(workflow_config, state_machine_config)
    
    # 测试配置验证
    errors = workflow.validate_config()
    if errors:
        print(f"工作流配置验证失败: {errors}")
        return False
    else:
        print("工作流配置验证成功")
    
    # 测试执行
    initial_state = {}
    result_state = workflow.execute(initial_state)
    
    # 验证执行结果
    assert result_state.get("started") == True
    assert result_state.get("processed") == True
    assert result_state.get("current_state") == "end"
    print("工作流执行测试通过")
    
    # 测试当前状态信息
    current_state_info = workflow.get_current_state_info()
    assert current_state_info["name"] == "end"
    assert current_state_info["type"] == "end"
    print("当前状态信息测试通过")
    
    # 测试重置
    workflow.reset()
    assert workflow.current_state == "start"
    print("重置功能测试通过")
    
    return True


def test_state_machine_factory():
    """测试状态机工作流工厂"""
    print("\n=== 测试状态机工作流工厂 ===")
    
    # 创建测试工作流类
    class TestWorkflow(StateMachineWorkflow):
        def handle_process(self, state, config):
            state["processed"] = True
            return state
    
    # 注册工作流
    factory = StateMachineWorkflowFactory()
    factory.register_workflow_type("test_workflow", TestWorkflow)
    
    # 创建工作流配置
    workflow_config = WorkflowConfig(
        name="test_workflow",
        description="测试工作流",
        version="1.0.0",
        nodes={},
        edges=[],
        entry_point="start"
    )
    
    # 创建工作流实例
    workflow = factory.create_workflow(workflow_config)
    
    # 验证实例创建
    assert isinstance(workflow, TestWorkflow)
    print("工作流实例创建测试通过")
    
    # 测试工厂方法
    factory = StateMachineWorkflowFactory()
    factory.register_workflow_type("test_workflow2", TestWorkflow)
    
    registered_workflows = factory.get_supported_types()
    assert "test_workflow2" in registered_workflows
    print("工厂注册功能测试通过")
    
    # 测试注销
    factory._workflow_classes.pop("test_workflow2", None)
    assert "test_workflow2" not in factory.get_supported_types()
    print("工厂注销功能测试通过")
    
    return True


def test_deep_thinking_compatibility():
    """测试深度思考工作流兼容性"""
    print("\n=== 测试深度思考工作流兼容性 ===")
    
    # 创建深度思考工作流类
    class DeepThinkingWorkflow(StateMachineWorkflow):
        def handle_problem_analysis(self, state, config):
            """问题分析状态处理"""
            state["problem_analyzed"] = True
            state["analysis_result"] = "问题分析完成"
            return state
        
        def handle_plan_generation(self, state, config):
            """计划生成状态处理"""
            state["plan_generated"] = True
            state["plan"] = "执行计划已生成"
            return state
        
        def handle_deep_thinking(self, state, config):
            """深度思考状态处理"""
            state["deep_thinking_completed"] = True
            state["thinking_result"] = "深度思考完成"
            return state
        
        def handle_solution_validation(self, state, config):
            """方案验证状态处理"""
            state["solution_validated"] = True
            state["validation_result"] = "方案验证通过"
            return state
    
    # 注册工作流
    factory = StateMachineWorkflowFactory()
    factory.register_workflow_type("deep_thinking", DeepThinkingWorkflow)
    
    # 创建工作流配置
    workflow_config = WorkflowConfig(
        name="deep_thinking",
        description="深度思考工作流",
        version="1.0.0",
        nodes={},
        edges=[],
        entry_point="initial"
    )
    
    # 创建工作流实例
    workflow = factory.create_workflow(workflow_config)
    
    # 执行工作流
    initial_state = {"problem": "需要解决的问题"}
    result_state = workflow.execute(initial_state)
    
    # 验证执行结果
    assert result_state.get("problem_analyzed") == True
    assert result_state.get("plan_generated") == True
    assert result_state.get("deep_thinking_completed") == True
    assert result_state.get("solution_validated") == True
    assert result_state.get("current_state") == "final"
    print("深度思考工作流执行测试通过")
    
    return True


def main():
    """主测试函数"""
    print("开始状态机工作流测试...")
    
    tests = [
        test_state_machine_config,
        test_state_machine_workflow,
        test_state_machine_factory,
        test_deep_thinking_compatibility
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print(f"✓ {test.__name__} 通过")
            else:
                failed += 1
                print(f"✗ {test.__name__} 失败")
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} 异常: {e}")
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"总计: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！状态机工作流基类实现成功。")
        return True
    else:
        print(f"\n❌ 有 {failed} 个测试失败，需要修复。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)