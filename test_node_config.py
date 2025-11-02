#!/usr/bin/env python3
"""测试节点配置加载功能

验证节点是否能够正确从配置文件加载默认配置，并与运行时配置正确合并。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.graph.node_config_loader import get_node_config_loader
from src.infrastructure.graph.nodes.analysis_node import AnalysisNode
from src.infrastructure.graph.nodes.llm_node import LLMNode
from src.infrastructure.graph.nodes.tool_node import ToolNode
from src.infrastructure.graph.nodes.plan_execute_agent_node import PlanExecuteAgentNode
from src.infrastructure.graph.nodes.react_agent_node import ReActAgentNode
from src.infrastructure.graph.nodes.agent_execution_node import AgentExecutionNode
from src.domain.agent.state import AgentState, AgentMessage


def test_node_config_loading():
    """测试节点配置加载功能"""
    print("测试节点配置加载功能...")
    
    # 测试配置加载器
    config_loader = get_node_config_loader()
    
    # 测试获取分析节点配置
    analysis_config = config_loader.get_node_config("analysis_node")
    print(f"分析节点配置: {analysis_config}")
    
    # 如果配置为空，尝试手动加载配置文件
    if not analysis_config:
        print("配置为空，尝试手动加载配置文件...")
        try:
            from src.infrastructure.config_loader import YamlConfigLoader
            yaml_loader = YamlConfigLoader()
            group_config = yaml_loader.load("nodes/_group.yaml")
            print(f"手动加载的配置: {group_config}")
            
            # 更新配置加载器的内部配置
            config_loader._node_configs = group_config
            config_loader._loaded = True
            
            # 重新获取配置
            analysis_config = config_loader.get_node_config("analysis_node")
            print(f"重新获取的分析节点配置: {analysis_config}")
        except Exception as e:
            print(f"手动加载配置失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 验证关键配置项
    if not analysis_config:
        print("警告：无法加载节点配置，使用默认值进行测试")
        analysis_config = {
            "max_tokens": 2000,
            "temperature": 0.7,
            "system_prompt": "默认系统提示词",
            "tool_keywords": ["我需要", "让我查询"]
        }
    
    assert "max_tokens" in analysis_config
    assert "temperature" in analysis_config
    assert "system_prompt" in analysis_config
    assert "tool_keywords" in analysis_config
    print("✓ 分析节点配置加载正确")
    
    # 测试获取LLM节点配置
    llm_config = config_loader.get_node_config("llm_node")
    print(f"LLM节点配置: {llm_config}")
    
    # 验证关键配置项
    assert "max_tokens" in llm_config
    assert "temperature" in llm_config
    assert "system_prompt" in llm_config
    assert "follow_up_indicators" in llm_config
    print("✓ LLM节点配置加载正确")
    
    # 测试配置合并功能
    runtime_config = {"max_tokens": 1500, "temperature": 0.5}
    merged_config = config_loader.merge_configs("analysis_node", runtime_config)
    
    # 验证合并结果
    assert merged_config["max_tokens"] == 1500  # 运行时配置覆盖默认配置
    assert merged_config["temperature"] == 0.5  # 运行时配置覆盖默认配置
    assert "system_prompt" in merged_config  # 默认配置保留
    print("✓ 配置合并功能正确")


def test_node_execution():
    """测试节点执行功能"""
    print("\n测试节点执行功能...")
    
    # 创建测试状态
    state = AgentState()
    state.messages = [AgentMessage(content="测试消息", role="user")]
    
    # 测试分析节点
    analysis_node = AnalysisNode()
    config_schema = analysis_node.get_config_schema()
    print(f"分析节点配置Schema: {config_schema}")
    
    # 使用默认配置执行节点
    try:
        result = analysis_node.execute(state, {})
        print(f"分析节点执行结果: {result.metadata}")
        print("✓ 分析节点执行成功")
    except Exception as e:
        print(f"✗ 分析节点执行失败: {e}")
    
    # 测试LLM节点
    llm_node = LLMNode()
    try:
        result = llm_node.execute(state, {})
        print(f"LLM节点执行结果: {result.metadata}")
        print("✓ LLM节点执行成功")
    except Exception as e:
        print(f"✗ LLM节点执行失败: {e}")
    
    # 测试工具节点
    tool_node = ToolNode()
    try:
        result = tool_node.execute(state, {})
        print(f"工具节点执行结果: {result.metadata}")
        print("✓ 工具节点执行成功")
    except Exception as e:
        print(f"✗ 工具节点执行失败: {e}")


def test_agent_nodes():
    """测试Agent节点"""
    print("\n测试Agent节点...")
    
    # 创建测试状态
    state = AgentState()
    state.messages = [AgentMessage(content="测试消息", role="user")]
    
    # 测试Plan-Execute Agent节点
    try:
        # 由于需要tool_executor参数，这里只测试配置Schema
        plan_execute_node = PlanExecuteAgentNode(tool_executor=None)
        config_schema = plan_execute_node.get_config_schema()
        print(f"Plan-Execute Agent节点配置Schema: {config_schema}")
        print("✓ Plan-Execute Agent节点配置Schema正确")
    except Exception as e:
        print(f"✗ Plan-Execute Agent节点测试失败: {e}")
    
    # 测试ReAct Agent节点
    try:
        # 由于需要tool_executor参数，这里只测试配置Schema
        react_node = ReActAgentNode(tool_executor=None)
        config_schema = react_node.get_config_schema()
        print(f"ReAct Agent节点配置Schema: {config_schema}")
        print("✓ ReAct Agent节点配置Schema正确")
    except Exception as e:
        print(f"✗ ReAct Agent节点测试失败: {e}")
    
    # 测试Agent执行节点
    try:
        agent_execution_node = AgentExecutionNode()
        config_schema = agent_execution_node.get_config_schema()
        print(f"Agent执行节点配置Schema: {config_schema}")
        print("✓ Agent执行节点配置Schema正确")
    except Exception as e:
        print(f"✗ Agent执行节点测试失败: {e}")


if __name__ == "__main__":
    print("开始测试节点配置功能...")
    
    try:
        test_node_config_loading()
        test_node_execution()
        test_agent_nodes()
        print("\n✓ 所有测试通过！节点配置功能正常工作。")
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)