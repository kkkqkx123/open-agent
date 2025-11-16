#!/usr/bin/env python3
"""测试状态管理器改进后的实现"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.di.unified_container import UnifiedContainerManager
from src.domain.state.interfaces import IStateCrudManager, IStateLifecycleManager
from src.infrastructure.graph.states.workflow import create_workflow_state


def test_state_managers_integration():
    """测试状态管理器和协作管理器的集成"""
    print("开始测试状态管理器集成...")
    
    try:
        # 创建依赖注入容器
        manager = UnifiedContainerManager()
        # 注册基础设施和域模块
        from src.infrastructure.di.infrastructure_module import InfrastructureModule
        from src.domain.di.domain_module import DomainModule
        manager.register_module(InfrastructureModule())
        manager.register_module(DomainModule())
        container = manager.configure_all_layers(environment="test")
        print("✓ 依赖注入容器创建成功")
        
        # 验证IStateCrudManager已注册
        assert container.has_service(IStateCrudManager), "IStateCrudManager未注册"
        print("✓ IStateCrudManager已注册")
        
        # 验证IStateLifecycleManager已注册
        assert container.has_service(IStateLifecycleManager), "IStateLifecycleManager未注册"
        print("✓ IStateLifecycleManager已注册")
        
        # 获取服务实例
        crud_manager = container.get(IStateCrudManager)
        lifecycle_manager = container.get(IStateLifecycleManager)
        print("✓ 服务实例获取成功")
        
        # 创建测试状态
        test_state = create_workflow_state(
            workflow_id="test_workflow",
            workflow_name="Test Workflow",
            input_text="测试输入",
            max_iterations=5
        )
        print("✓ 测试状态创建成功")
        
        # 测试状态创建
        print("\n=== 测试状态创建 ===")
        state_id = crud_manager.create_state(test_state)
        print(f"✓ 状态创建成功: {state_id}")
        
        # 测试状态检索
        print("\n=== 测试状态检索 ===")
        retrieved_state = crud_manager.get_state(state_id)
        assert retrieved_state is not None, "状态检索失败"
        print(f"✓ 状态检索成功: {retrieved_state.id}")
        
        # 测试状态更新
        print("\n=== 测试状态更新 ===")
        retrieved_state.messages.append({"role": "user", "content": "测试消息"})
        update_success = crud_manager.update_state(state_id, retrieved_state)
        assert update_success, "状态更新失败"
        print("✓ 状态更新成功")
        
        # 测试生命周期管理器
        print("\n=== 测试生命周期管理器 ===")
        
        # 验证域状态
        is_valid = lifecycle_manager.validate_domain_state(state_id)
        assert is_valid, "域状态验证失败"
        print("✓ 域状态验证成功")
        
        # 创建快照
        snapshot_id = lifecycle_manager.create_snapshot(state_id)
        print(f"✓ 快照创建成功: {snapshot_id}")
        
        # 恢复快照
        restore_success = lifecycle_manager.restore_snapshot(state_id, snapshot_id)
        assert restore_success, "快照恢复失败"
        print("✓ 快照恢复成功")
        
        # 记录状态变更
        change_recorded = lifecycle_manager.record_state_change(
            state_id, "test_change", {"key": "value"}
        )
        assert change_recorded, "状态变更记录失败"
        print("✓ 状态变更记录成功")
        
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
        manager = UnifiedContainerManager()
        # 注册基础设施和域模块
        from src.infrastructure.di.infrastructure_module import InfrastructureModule
        from src.domain.di.domain_module import DomainModule
        manager.register_module(InfrastructureModule())
        manager.register_module(DomainModule())
        container = manager.configure_all_layers(environment="test")
        crud_manager = container.get(IStateCrudManager)
        
        # 测试状态创建
        from src.infrastructure.graph.states.workflow import create_workflow_state
        test_state = create_workflow_state(
            workflow_id="test_workflow",
            workflow_name="Test Workflow",
            input_text="测试输入",
            max_iterations=10
        )
        
        state_id = crud_manager.create_state(test_state)
        assert state_id is not None, "状态创建失败"
        print("✓ 状态创建成功")
        
        # 验证获取的状态
        retrieved_state = crud_manager.get_state(state_id)
        assert retrieved_state is not None, "状态获取失败"
        print("✓ 状态获取成功")
        
        # 测试状态更新
        retrieved_state.messages.append({"role": "user", "content": "测试消息"})
        update_success = crud_manager.update_state(state_id, retrieved_state)
        assert update_success, "状态更新失败"
        print("✓ 状态更新成功")
        
        # 验证更新后的状态
        updated_state = crud_manager.get_state(state_id)
        assert updated_state is not None, "状态更新后获取失败"
        print("✓ 状态更新验证成功")
        
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