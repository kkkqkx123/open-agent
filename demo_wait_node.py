#!/usr/bin/env python3
"""
等待节点演示脚本

展示如何使用新的等待节点替代原来的LLM节点进行人工审核。
"""

import time
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.infrastructure.graph.nodes.wait_node import WaitNode, TimeoutStrategy
from src.domain.agent.state import AgentState, AgentMessage


def demo_basic_wait():
    """演示基本等待功能"""
    print("=== 基本等待功能演示 ===")
    
    # 创建等待节点
    wait_node = WaitNode()
    
    # 创建状态
    state = AgentState()
    state.agent_id = "demo_agent"
    state.messages = []
    
    # 配置等待节点
    config = {
        "timeout_enabled": False,  # 禁用超时以便演示
        "wait_message": "等待人工审核中...",
        "auto_resume_key": "review_result"
    }
    
    print("1. 开始等待...")
    result = wait_node.execute(state, config)
    
    print(f"   - 等待状态: {result.metadata['is_waiting']}")
    print(f"   - 等待消息: {result.metadata['wait_message']}")
    print(f"   - 下一步: {result.next_node}")
    print(f"   - 系统消息: {state.messages[-1].content}")
    
    print("\n2. 模拟外部输入（人工审核通过）...")
    state.review_result = "approved"
    
    result = wait_node.execute(state, config)
    print(f"   - 等待状态: {result.metadata['is_waiting']}")
    print(f"   - 恢复原因: {result.metadata['resume_value']}")
    print(f"   - 下一步: {result.next_node}")
    print(f"   - 系统消息: {state.messages[-1].content}")


def demo_timeout_strategies():
    """演示超时处理策略"""
    print("\n=== 超时处理策略演示 ===")
    
    wait_node = WaitNode()
    
    # 演示继续等待策略
    print("\n1. 继续等待策略演示")
    state = AgentState()
    state.agent_id = "demo_agent"
    state.messages = []
    
    config = {
        "timeout_enabled": True,
        "timeout_seconds": 2,  # 2秒超时
        "timeout_strategy": "continue_waiting",
        "wait_message": "等待审核中..."
    }
    
    print("   - 开始等待（2秒超时）...")
    result = wait_node.execute(state, config)
    wait_id = result.metadata["wait_id"]
    
    print("   - 等待超时中...")
    time.sleep(2.5)  # 等待超时
    
    result = wait_node.execute(state, config)
    print(f"   - 超时处理: {result.metadata['strategy']}")
    print(f"   - 继续等待: {result.next_node == '__wait__'}")
    print(f"   - 超时消息: {state.messages[-1].content}")
    
    # 清理等待状态
    wait_node.clear_wait_state(wait_id)


def demo_routing_rules():
    """演示路由规则"""
    print("\n=== 路由规则演示 ===")
    
    wait_node = WaitNode()
    
    # 测试不同的审核结果
    test_cases = [
        ("approved", "最终答案"),
        ("rejected", "重新分析"),
        ("modify", "修改结果"),
        ("unknown", "默认节点")
    ]
    
    for review_result, expected_desc in test_cases:
        print(f"\n测试审核结果: {review_result}")
        
        state = AgentState()
        state.agent_id = "demo_agent"
        state.messages = []
        state.review_result = review_result
        
        config = {
            "timeout_enabled": False,
            "auto_resume_key": "review_result",
            "routing_rules": {
                "approved": "final_answer",
                "rejected": "analyze",
                "modify": "modify_result"
            },
            "default_next_node": "default_node"
        }
        
        result = wait_node.execute(state, config)
        print(f"   - 路由到: {result.next_node}")
        print(f"   - 预期: {expected_desc}")


def demo_cache_and_exit():
    """演示缓存并退出策略"""
    print("\n=== 缓存并退出策略演示 ===")
    
    wait_node = WaitNode()
    
    state = AgentState()
    state.agent_id = "demo_agent"
    state.messages = []
    state.current_task = "需要人工审核的任务"
    
    config = {
        "timeout_enabled": True,
        "timeout_seconds": 2,
        "timeout_strategy": "cache_and_exit",
        "wait_message": "等待长时间审核..."
    }
    
    print("1. 开始等待（2秒超时，缓存并退出）...")
    result = wait_node.execute(state, config)
    wait_id = result.metadata["wait_id"]
    
    print("2. 等待超时...")
    time.sleep(2.5)
    
    result = wait_node.execute(state, config)
    print(f"   - 超时处理: {result.metadata['strategy']}")
    print(f"   - 退出工作流: {result.next_node == '__exit__'}")
    print(f"   - 状态已缓存: {result.metadata['cached']}")
    print(f"   - 系统消息: {state.messages[-1].content}")
    
    print("3. 检查缓存的状态...")
    cached_state = wait_node.get_cached_state(wait_id)
    if cached_state:
        print(f"   - 缓存的Agent ID: {cached_state['agent_id']}")
        print(f"   - 缓存的任务: {cached_state['current_task']}")
        print(f"   - 缓存的消息数: {len(cached_state['messages'])}")
    
    # 清理
    wait_node.clear_wait_state(wait_id)


def demo_llm_continue():
    """演示LLM继续策略"""
    print("\n=== LLM继续策略演示 ===")
    
    wait_node = WaitNode()
    
    state = AgentState()
    state.agent_id = "demo_agent"
    state.messages = []
    
    config = {
        "timeout_enabled": True,
        "timeout_seconds": 2,
        "timeout_strategy": "llm_continue",
        "wait_message": "等待审核中...",
        "continue_node": "analyze"
    }
    
    print("1. 开始等待（2秒超时，LLM继续）...")
    result = wait_node.execute(state, config)
    
    print("2. 等待超时...")
    time.sleep(2.5)
    
    result = wait_node.execute(state, config)
    print(f"   - 超时处理: {result.metadata['strategy']}")
    print(f"   - 自动继续: {result.metadata['auto_continue']}")
    print(f"   - 继续到节点: {result.next_node}")
    print(f"   - 等待状态: {state.is_waiting}")
    print(f"   - 继续原因: {state.continue_reason}")
    print(f"   - 系统消息: {state.messages[-1].content}")


def demo_config_validation():
    """演示配置验证"""
    print("\n=== 配置验证演示 ===")
    
    wait_node = WaitNode()
    
    # 有效配置
    valid_config = {
        "timeout_enabled": True,
        "timeout_seconds": 300,
        "timeout_strategy": "continue_waiting",
        "wait_message": "测试消息",
        "routing_rules": {"approved": "final"}
    }
    
    errors = wait_node.validate_config(valid_config)
    print(f"有效配置验证结果: {len(errors)} 个错误")
    
    # 无效配置
    invalid_configs = [
        {"timeout_strategy": "invalid_strategy"},
        {"timeout_seconds": -1},
        {"routing_rules": "not_a_dict"}
    ]
    
    for i, config in enumerate(invalid_configs, 1):
        errors = wait_node.validate_config(config)
        print(f"无效配置 {i} 验证结果: {len(errors)} 个错误")
        for error in errors:
            print(f"   - {error}")


def main():
    """主演示函数"""
    print("等待节点功能演示")
    print("=" * 50)
    
    try:
        demo_basic_wait()
        demo_timeout_strategies()
        demo_routing_rules()
        demo_cache_and_exit()
        demo_llm_continue()
        demo_config_validation()
        
        print("\n" + "=" * 50)
        print("演示完成！")
        print("\n主要优势:")
        print("✅ 真正的等待机制，不消耗LLM资源")
        print("✅ 灵活的超时处理策略")
        print("✅ 丰富的配置选项")
        print("✅ 完整的状态管理")
        print("✅ 外部输入触发恢复")
        print("✅ 状态缓存和恢复功能")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()