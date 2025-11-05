#!/usr/bin/env python3
"""测试合并后的插件系统

验证plugins和hooks模块合并后的功能是否正常工作。
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from infrastructure.graph.plugins import (
    PluginManager, PluginType, PluginContext, HookContext, HookPoint
)
from infrastructure.graph.states.base import BaseGraphState, create_base_state


def test_plugin_manager_initialization():
    """测试插件管理器初始化"""
    print("测试插件管理器初始化...")
    
    manager = PluginManager()
    success = manager.initialize()
    
    assert success, "插件管理器初始化失败"
    print("✓ 插件管理器初始化成功")
    
    # 检查统计信息
    stats = manager.get_manager_stats()
    print(f"✓ 插件统计: {stats['total_plugins']} 个插件")
    print(f"  - START插件: {stats['by_type']['start']} 个")
    print(f"  - END插件: {stats['by_type']['end']} 个")
    print(f"  - HOOK插件: {stats['by_type']['hook']} 个")
    
    return manager


def test_start_plugins(manager):
    """测试START插件执行"""
    print("\n测试START插件执行...")
    
    # 创建测试状态和上下文
    state = {"test": "data"}
    context = PluginContext(
        workflow_id="test-workflow-001",
        thread_id="test-thread-001",
        session_id="test-session-001"
    )
    
    # 执行START插件
    updated_state = manager.execute_plugins(PluginType.START, state, context)
    
    # 验证结果
    assert "context_summary" in updated_state, "缺少context_summary"
    assert "environment_check" in updated_state, "缺少environment_check"
    assert "start_metadata" in updated_state, "缺少start_metadata"
    
    print("✓ START插件执行成功")
    print(f"  - 上下文摘要长度: {len(updated_state.get('context_summary', ''))}")
    print(f"  - 环境检查通过: {updated_state.get('environment_check', {}).get('passed', False)}")
    
    return updated_state


def test_hook_plugins(manager):
    """测试Hook插件执行"""
    print("\n测试Hook插件执行...")
    
    # 创建测试状态和上下文
    state = create_base_state()
    state["iteration_count"] = 1
    state["tool_calls"] = []
    
    context = HookContext(
        node_type="llm_node",
        state=state,
        config={"test": "config"},
        hook_point=HookPoint.BEFORE_EXECUTE
    )
    
    # 执行Hook插件
    result = manager.execute_hooks(HookPoint.BEFORE_EXECUTE, context)
    
    # 验证结果
    assert result.should_continue, "Hook执行应该继续"
    assert "executed_hooks" in result.metadata, "缺少executed_hooks"
    
    print("✓ Hook插件执行成功")
    print(f"  - 执行的Hook数量: {len(result.metadata['executed_hooks'])}")
    
    for hook_info in result.metadata["executed_hooks"]:
        print(f"    - {hook_info['plugin_name']}: {hook_info['execution_time']:.4f}s")
    
    return result


def test_end_plugins(manager, state):
    """测试END插件执行"""
    print("\n测试END插件执行...")
    
    # 创建测试上下文
    context = PluginContext(
        workflow_id="test-workflow-001",
        thread_id="test-thread-001",
        session_id="test-session-001"
    )
    
    # 执行END插件
    updated_state = manager.execute_plugins(PluginType.END, state, context)
    
    # 验证结果
    assert "result_summary" in updated_state, "缺少result_summary"
    assert "end_metadata" in updated_state, "缺少end_metadata"
    
    print("✓ END插件执行成功")
    print(f"  - 结果摘要长度: {len(updated_state.get('result_summary', ''))}")
    
    return updated_state


def test_plugin_configuration():
    """测试插件配置"""
    print("\n测试插件配置...")
    
    # 创建自定义配置
    custom_config = {
        "start_plugins": {
            "builtin": [
                {"name": "context_summary", "enabled": True, "priority": 10, "config": {
                    "max_summary_length": 500
                }},
                {"name": "environment_check", "enabled": True, "priority": 20, "config": {
                    "fail_on_error": False
                }}
            ]
        },
        "hook_plugins": {
            "global": [
                {"name": "performance_monitoring", "enabled": True, "priority": 10, "config": {
                    "timeout_threshold": 5.0
                }},
                {"name": "logging", "enabled": True, "priority": 20, "config": {
                    "log_level": "DEBUG"
                }}
            ]
        }
    }
    
    # 创建配置文件
    import json
    config_path = "test_plugin_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(custom_config, f, indent=2, ensure_ascii=False)
    
    try:
        # 使用自定义配置初始化管理器
        manager = PluginManager(config_path=config_path)
        success = manager.initialize()
        
        assert success, "使用自定义配置初始化失败"
        print("✓ 自定义配置加载成功")
        
        # 测试配置是否生效
        start_plugins = manager.get_enabled_plugins(PluginType.START)
        assert len(start_plugins) == 2, f"应该有2个START插件，实际有{len(start_plugins)}个"
        
        hook_plugins = manager.get_enabled_hook_plugins("llm_node")
        assert len(hook_plugins) >= 1, f"应该至少有1个Hook插件，实际有{len(hook_plugins)}个"
        
        print("✓ 插件配置验证成功")
        
    finally:
        # 清理测试文件
        if os.path.exists(config_path):
            os.remove(config_path)


def test_hook_execution_flow(manager):
    """测试Hook执行流程"""
    print("\n测试Hook执行流程...")
    
    # 创建测试状态
    state = create_base_state()
    state["iteration_count"] = 1
    
    # 模拟节点执行函数
    def mock_node_executor(state, config):
        from infrastructure.graph.registry import NodeExecutionResult
        return NodeExecutionResult(
            state=state,
            next_node="next_node",
            metadata={"execution_result": "success"}
        )
    
    # 使用统一的Hook执行接口
    result = manager.execute_with_hooks(
        node_type="llm_node",
        state=state,
        config={"test": "config"},
        node_executor_func=mock_node_executor
    )
    
    # 验证结果
    assert result is not None, "执行结果不能为None"
    assert result.next_node == "next_node", "下一个节点不正确"
    
    print("✓ Hook执行流程测试成功")
    print(f"  - 下一个节点: {result.next_node}")
    print(f"  - 执行元数据: {result.metadata}")
    
    return result


def main():
    """主测试函数"""
    print("=" * 60)
    print("开始测试合并后的插件系统")
    print("=" * 60)
    
    try:
        # 测试插件管理器初始化
        manager = test_plugin_manager_initialization()
        
        # 测试START插件
        state = test_start_plugins(manager)
        
        # 测试Hook插件
        test_hook_plugins(manager)
        
        # 测试Hook执行流程
        test_hook_execution_flow(manager)
        
        # 测试END插件
        test_end_plugins(manager, state)
        
        # 测试插件配置
        test_plugin_configuration()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！插件系统合并成功！")
        print("=" * 60)
        
        # 清理资源
        manager.cleanup()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()