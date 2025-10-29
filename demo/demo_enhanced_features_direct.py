"""直接演示增强功能

通过直接导入模块来避免复杂的导入路径问题。
"""

import tempfile
import os
import sys
from pathlib import Path

# 直接导入我们实现的模块
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# 直接导入增强管理器
from src.infrastructure.graph.states.composite_manager import (
    CompositeStateManager as EnhancedStateManager,
    create_composite_state_manager as create_enhanced_state_manager,
)
from src.infrastructure.graph.states.interface import (
    ConflictType,
    ConflictResolutionStrategy
)

# 直接导入增强验证器
from infrastructure.config.enhanced_validator import (
    EnhancedConfigValidator,
    create_enhanced_config_validator,
    ValidationLevel,
    ValidationSeverity
)

# 创建简单的AgentState类来避免复杂导入
class SimpleAgentState(dict):
    """简化的Agent状态类"""
    pass

def create_simple_agent_state(input_text: str) -> SimpleAgentState:
    """创建简单的Agent状态"""
    state = SimpleAgentState()
    state["input"] = input_text
    state["output"] = None
    state["tool_calls"] = []
    state["tool_results"] = []
    state["iteration_count"] = 0
    state["max_iterations"] = 10
    state["errors"] = []
    state["complete"] = False
    state["metadata"] = {}
    return state

def demo_enhanced_state_manager_direct():
    """直接演示增强状态管理器功能"""
    print("=" * 60)
    print("增强状态管理器直接演示")
    print("=" * 60)
    
    # 创建增强的状态管理器
    manager = create_enhanced_state_manager(
        conflict_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS
    )
    
    # 创建测试状态
    state1 = create_simple_agent_state("原始输入")
    state2 = create_simple_agent_state("修改后的输入")
    
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
        # 为每种策略创建新的管理器实例，因为CompositeStateManager不支持直接修改策略
        temp_manager = create_enhanced_state_manager(conflict_strategy=strategy)
        resolved_state, _ = temp_manager.update_state_with_conflict_resolution(state1, state2)
        print(f"  {strategy.value}: {resolved_state['input']}")
    
    # 状态版本控制
    # 使用正确的参数顺序：先state_id，再state，最后是metadata
    version_id = manager.create_state_version("resolved_state", resolved_state, {"description": "解决冲突后的状态"})
    print(f"\n创建状态版本: {version_id}")
    
    # 获取版本历史
    history = manager.get_conflict_history()
    print(f"冲突历史记录: {len(history)} 条")


def demo_enhanced_config_validator_direct():
    """直接演示增强配置验证器功能"""
    print("\n" + "=" * 60)
    print("增强配置验证器直接演示")
    print("=" * 60)
    
    # 创建增强的配置验证器
    validator = create_enhanced_config_validator()
    
    # 测试配置数据
    test_configs = [
        {
            "name": "valid_config",
            "version": "1.0.0",
            "nodes": {"node1": {"type": "input"}}
        },
        {
            "name": "invalid_config"
            # 缺少version和nodes字段
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
        """)
        temp_file = f.name
    
    try:
        report = validator.validate_config(temp_file)
        print(f"配置文件验证结果: {'有效' if report.is_valid() else '无效'}")
    finally:
        os.unlink(temp_file)


def main():
    """主演示函数"""
    print("Modular Agent Framework - 第一阶段优化功能直接演示")
    print("实现内容:")
    print("1. EnhancedStateManager - 状态冲突解决基础框架")
    print("2. EnhancedConfigValidator - 多层次配置验证框架")
    print("3. 单元测试覆盖 - 确保功能正确性")
    print("4. 系统集成 - 依赖注入配置")
    print()
    
    demo_enhanced_state_manager_direct()
    demo_enhanced_config_validator_direct()
    
    print("\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)


if __name__ == "__main__":
    main()