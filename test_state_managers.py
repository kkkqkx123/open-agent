#!/usr/bin/env python3
"""测试状态管理器改进后的实现"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.di_config import create_container
from src.domain.state.interfaces import IStateManager, IStateCollaborationManager
from src.infrastructure.graph.states.workflow import create_workflow_state


def test_state_managers_integration():
    """测试状态管理器和协作管理器的集成"""
    print("开始测试状态管理器集成...")
    
    try:
        # 创建依赖注入容器
        container = create_container()
        print("✓ 依赖注入容器创建成功")
        
        # 验证StateManager已注册
        assert container.has_service(IStateManager), "StateManager未注册"
        print("✓ StateManager已注册")
        
        # 验证StateCollaborationManager已注册
        assert container.has_service(IStateCollaborationManager), "StateCollaborationManager未注册"
        print("✓ StateCollaborationManager已注册")
        
        # 获取服务实例
        state_manager = container.get(IStateManager)
        collaboration_manager = container.get(IStateCollaborationManager)
        print("✓ 服务实例获取成功")
        
        # 验证CollaborationManager使用了正确的StateManager
        assert collaboration_manager.state_manager is state_manager, "CollaborationManager未使用正确的StateManager"
        print("✓ CollaborationManager正确使用了StateManager")
        
        # 创建测试状态
        test_state = create_workflow_state(
            workflow_id="test_workflow",
            workflow_name="Test Workflow",
            input_text="测试输入",
            max_iterations=5
        )
        print("✓ 测试状态创建成功")
        
        # 测试状态验证
        validation_errors = collaboration_manager.validate_domain_state(test_state)
        assert not validation_errors, f"状态验证失败: {validation_errors}"
        print("✓ 状态验证通过")
        
        # 测试执行流程
        def test_executor(state):
            """测试执行函数"""
            # 修改状态
            state["iteration_count"] += 1
            state["output"] = "测试输出"
            return state
        
        result_state = collaboration_manager.execute_with_state_management(
            test_state,
            test_executor,
            context={"test": True}
        )
        print("✓ 状态管理执行成功")
        
        # 验证状态变化
        assert result_state["iteration_count"] == 1, "迭代计数未正确更新"
        assert result_state["output"] == "测试输出", "输出未正确设置"
        print("✓ 状态变化验证通过")
        
        # 测试快照功能
        snapshot_id = collaboration_manager.create_snapshot(result_state, "测试快照")
        assert snapshot_id, "快照创建失败"
        print("✓ 快照创建成功")
        
        # 测试快照恢复
        restored_state = collaboration_manager.restore_snapshot(snapshot_id)
        assert restored_state, "快照恢复失败"
        assert restored_state["output"] == "测试输出", "快照恢复状态不正确"
        print("✓ 快照恢复成功")
        
        # 测试性能统计
        stats = collaboration_manager.get_performance_stats()
        assert "total_agents" in stats, "性能统计缺少total_agents字段"
        assert "total_snapshots" in stats, "性能统计缺少total_snapshots字段"
        assert stats["total_snapshots"] >= 1, "快照数量统计不正确"
        print("✓ 性能统计获取成功")
        
        print("\n所有测试通过！状态管理器改进成功。")
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"StateManager基础功能测试失败: {e}"


def test_state_manager_basic_functionality():
    """测试StateManager基础功能"""
    print("\n开始测试StateManager基础功能...")
    
    try:
        # 创建依赖注入容器
        container = create_container()
        state_manager = container.get(IStateManager)
        
        # 测试状态创建
        test_state = {
            "messages": [],
            "tool_results": [],
            "current_step": "start",
            "max_iterations": 10,
            "iteration_count": 0
        }
        
        state_id = "test_state_1"
        created_state = state_manager.create_state(state_id, test_state)
        assert created_state == test_state, "状态创建失败"
        print("✓ 状态创建成功")
        
        # 测试状态更新
        updates = {"iteration_count": 1, "current_step": "processing"}
        updated_state = state_manager.update_state(state_id, created_state, updates)
        assert updated_state["iteration_count"] == 1, "状态更新失败"
        assert updated_state["current_step"] == "processing", "状态更新失败"
        print("✓ 状态更新成功")
        
        # 测试状态获取
        retrieved_state = state_manager.get_state(state_id)
        assert retrieved_state == updated_state, "状态获取失败"
        print("✓ 状态获取成功")
        
        # 测试状态比较
        diff = state_manager.compare_states(created_state, updated_state)
        assert "modified" in diff, "状态比较失败"
        assert "iteration_count" in diff["modified"], "状态比较失败"
        print("✓ 状态比较成功")
        
        # 测试序列化/反序列化
        serialized = state_manager.serialize_state(updated_state)
        deserialized = state_manager.deserialize_state(serialized)
        assert deserialized == updated_state, "序列化/反序列化失败"
        print("✓ 序列化/反序列化成功")
        
        print("StateManager基础功能测试通过！")
        
    except Exception as e:
        print(f"StateManager基础功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"StateManager基础功能测试失败: {e}"


if __name__ == "__main__":
    print("=" * 60)
    print("状态管理器改进测试")
    print("=" * 60)
    
    # 运行基础功能测试
    basic_test_passed = test_state_manager_basic_functionality()
    
    # 运行集成测试
    integration_test_passed = test_state_managers_integration()
    
    print("\n" + "=" * 60)
    if basic_test_passed and integration_test_passed:
        print("所有测试通过！状态管理器改进成功。")
        sys.exit(0)
    else:
        print("部分测试失败，请检查实现。")
        sys.exit(1)