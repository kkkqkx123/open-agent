"""简化版增强优化功能演示脚本

直接导入模块，避免复杂的导入路径问题。
"""

import tempfile
import os
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# 直接导入需要的类
from infrastructure.graph.states.enhanced_manager import (
    EnhancedStateManager,
    create_enhanced_state_manager,
    ConflictType,
    ConflictResolutionStrategy
)
from infrastructure.config.enhanced_validator import (
    EnhancedConfigValidator,
    create_enhanced_config_validator,
    ValidationLevel,
    ValidationSeverity,
    ConfigFixer
)
from infrastructure.graph.state import create_agent_state


def demo_enhanced_state_manager():
    """演示增强状态管理器功能"""
    print("=" * 60)
    print("增强状态管理器演示")
    print("=" * 60)
    
    # 创建增强的状态管理器
    manager = create_enhanced_state_manager(
        conflict_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS
    )
    
    # 创建测试状态
    state1 = create_agent_state("原始输入")
    state2 = create_agent_state("修改后的输入")
    
    # 修改state2以创建冲突
    state2["input"] = "冲突输入"
    state2["custom_field"] = "新字段值"
    
    print("状态1:", {k: v for k, v in state1.items() if v is not None})
    print("状态2:", {k: v for k, v in state2.items() if v is not None})
    
    # 检测冲突
    conflicts = manager.detect_conflicts(state1, state2)
    print(f"检测到 {len(conflicts)} 个冲突:")
    for conflict in conflicts:
        print(f"  - {conflict.field_path}: {conflict.current_value} -> {conflict.new_value} ({conflict.conflict_type.value})")
    
    # 使用冲突解决策略更新状态
    resolved_state, unresolved = manager.update_state_with_conflict_resolution(state1, state2)
    print(f"解决冲突后的状态: {resolved_state['input']}")
    print(f"未解决的冲突: {len(unresolved)}")
    
    # 测试不同冲突解决策略
    print("\n不同冲突解决策略测试:")
    strategies = [
        ConflictResolutionStrategy.LAST_WRITE_WINS,
        ConflictResolutionStrategy.FIRST_WRITE_WINS,
        ConflictResolutionStrategy.MERGE_CHANGES
    ]
    
    for strategy in strategies:
        manager.conflict_resolver.strategy = strategy
        resolved_state, _ = manager.update_state_with_conflict_resolution(state1, state2)
        print(f"  {strategy.value}: {resolved_state['input']}")
    
    # 状态版本控制
    version_id = manager.create_state_version(resolved_state, {"description": "解决冲突后的状态"})
    print(f"\n创建状态版本: {version_id}")
    
    # 获取版本历史
    history = manager.get_conflict_history()
    print(f"冲突历史记录: {len(history)} 条")


def demo_enhanced_config_validator():
    """演示增强配置验证器功能"""
    print("\n" + "=" * 60)
    print("增强配置验证器演示")
    print("=" * 60)
    
    # 创建增强的配置验证器
    validator = create_enhanced_config_validator()
    
    # 测试配置数据
    test_configs = [
        {
            "name": "valid_config",
            "version": "1.0.0",
            "nodes": {"node1": {"type": "input"}},
            "edges": [{"from_node": "node1", "to_node": "__end__"}]
        },
        {
            "name": "invalid_config",
            # 缺少version和nodes字段
            "edges": [{"from_node": "nonexistent", "to_node": "__end__"}]  # 无效引用
        }
    ]
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n配置 {i} 验证结果:")
        report = validator.validate_config_data(config)
        
        print(f"  配置是否有效: {report.is_valid()}")
        print(f"  验证摘要: {report.summary}")
        
        for level, results in report.level_results.items():
            for result in results:
                status = "通过" if result.passed else "失败"
                print(f"  {level.value}: {status} - {result.message}")
    
    # 演示配置文件验证
    print("\n配置文件验证演示:")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
name: test_workflow
version: 1.0.0
nodes:
  start_node:
    type: input
  process_node:
    type: processor
edges:
  - from_node: start_node
    to_node: process_node
  - from_node: process_node
    to_node: __end__
        """)
        temp_file = f.name
    
    try:
        report = validator.validate_config(temp_file)
        print(f"配置文件验证结果: {'有效' if report.is_valid() else '无效'}")
        print(f"验证级别: {list(report.level_results.keys())}")
    finally:
        os.unlink(temp_file)


def main():
    """主演示函数"""
    print("Modular Agent Framework - 第一阶段优化功能演示")
    print("实现内容:")
    print("1. EnhancedStateManager - 状态冲突解决基础框架")
    print("2. EnhancedConfigValidator - 多层次配置验证框架")
    print("3. 单元测试覆盖 - 确保功能正确性")
    print("4. 系统集成 - 依赖注入配置")
    print()
    
    demo_enhanced_state_manager()
    demo_enhanced_config_validator()
    
    print("\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)


if __name__ == "__main__":
    main()