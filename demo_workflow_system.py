#!/usr/bin/env python3
"""
工作流系统演示脚本

展示如何使用YAML配置化工作流系统创建和执行工作流。
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.workflow.manager import WorkflowManager
from src.workflow.registry import NodeRegistry, register_node
from src.workflow.nodes.analysis_node import AnalysisNode
from src.workflow.nodes.tool_node import ToolNode
from src.workflow.nodes.llm_node import LLMNode
from src.workflow.nodes.condition_node import ConditionNode
from src.prompts.agent_state import AgentState, HumanMessage


def demo_basic_workflow() -> None:
    """演示基本工作流使用"""
    print("=" * 60)
    print("工作流系统演示 - 基本使用")
    print("=" * 60)
    
    # 创建工作流管理器
    manager = WorkflowManager()
    
    # 列出可用的节点类型
    print("\n可用的节点类型:")
    for node_type in manager.workflow_builder.list_available_nodes():
        print(f"  - {node_type}")
    
    # 加载ReAct工作流
    print("\n加载ReAct工作流配置...")
    try:
        workflow_id = manager.load_workflow("configs/workflows/react.yaml")
        print(f"✓ 工作流加载成功，ID: {workflow_id}")
        
        # 获取工作流配置信息
        config = manager.get_workflow_config(workflow_id)
        if config:
            print(f"  - 名称: {config.name}")
            print(f"  - 描述: {config.description}")
            print(f"  - 版本: {config.version}")
            print(f"  - 节点数: {len(config.nodes)}")
            print(f"  - 边数: {len(config.edges)}")
        
        # 获取工作流元数据
        metadata = manager.get_workflow_metadata(workflow_id)
        if metadata:
            print(f"  - 配置路径: {metadata.get('config_path')}")
            print(f"  - 加载时间: {metadata.get('loaded_at')}")
        
    except Exception as e:
        print(f"✗ 工作流加载失败: {e}")
        return
    
    # 创建初始状态
    print("\n创建初始状态...")
    initial_state = AgentState()
    initial_state.add_message(HumanMessage(content="请帮我查询今天的天气情况"))
    print(f"✓ 初始状态创建完成，消息数: {len(initial_state.messages)}")
    
    # 运行工作流
    print("\n运行工作流...")
    try:
        result = manager.run_workflow(workflow_id, initial_state)
        print(f"✓ 工作流执行完成")
        
        # 处理不同类型的结果
        if isinstance(result, dict):
            messages = result.get('messages', [])
            tool_results = result.get('tool_results', [])
            current_step = result.get('current_step', '')
        else:
            # AgentState 对象
            messages = result.messages
            tool_results = result.tool_results
            current_step = result.current_step
        
        print(f" - 最终消息数: {len(messages)}")
        print(f"  - 工具结果数: {len(tool_results)}")
        print(f"  - 当前步骤: {current_step}")
        
        # 显示最终消息
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, 'content'):
                content = getattr(last_message, 'content', '')
                print(f" - 最终响应: {content[:100]}...")
        
    except Exception as e:
        print(f"✗ 工作流执行失败: {e}")
        return
    
    # 显示工作流统计
    print("\n工作流统计:")
    workflows = manager.list_workflows()
    print(f" - 已加载工作流数: {len(workflows)}")
    
    for wf_id in workflows:
        metadata = manager.get_workflow_metadata(wf_id)
        if metadata:
            name = metadata.get('name', 'Unknown')
            usage_count = metadata.get('usage_count', 0)
            print(f" - {name}: 使用 {usage_count} 次")


def demo_plan_execute_workflow() -> None:
    """演示Plan-and-Execute工作流"""
    print("\n" + "=" * 60)
    print("工作流系统演示 - Plan-and-Execute模式")
    print("=" * 60)
    
    # 创建工作流管理器
    manager = WorkflowManager()
    
    # 加载Plan-and-Execute工作流
    print("\n加载Plan-and-Execute工作流配置...")
    try:
        workflow_id = manager.load_workflow("configs/workflows/plan_execute.yaml")
        print(f"✓ 工作流加载成功，ID: {workflow_id}")
        
        # 获取工作流配置信息
        config = manager.get_workflow_config(workflow_id)
        if config:
            print(f"  - 名称: {config.name}")
            print(f" - 描述: {config.description}")
            print(f"  - 节点数: {len(config.nodes)}") # type: ignore
            
            # 显示节点信息
            print("\n工作流节点:")
            for node_name, node_config in config.nodes.items(): # type: ignore
                print(f" - {node_name}: {node_config.type}")
        
    except Exception as e:
        print(f"✗ 工作流加载失败: {e}")
        return
    
    # 创建初始状态
    print("\n创建初始状态...")
    initial_state = AgentState()
    initial_state.add_message(HumanMessage(content="请帮我分析当前市场趋势并给出投资建议"))
    print(f"✓ 初始状态创建完成")
    
    # 运行工作流
    print("\n运行工作流...")
    try:
        result = manager.run_workflow(workflow_id, initial_state)
        print(f"✓ 工作流执行完成")
        print(f"  - 最终消息数: {len(result.messages)}")
        print(f"  - 工具结果数: {len(result.tool_results)}")
        
    except Exception as e:
        print(f"✗ 工作流执行失败: {e}")

def demo_custom_node() -> None:
    """演示自定义节点"""
    print("\n" + "=" * 60)
    print("工作流系统演示 - 自定义节点")
    print("=" * 60)
    
    from src.workflow.registry import BaseNode, NodeExecutionResult, register_node, node
    
    # 定义自定义节点
    @node("custom_greeting_node")
    class CustomGreetingNode(BaseNode):
        @property
        def node_type(self) -> str:
            return "custom_greeting_node"
        
        def execute(self, state: AgentState, config: dict) -> NodeExecutionResult:
            # 获取配置中的问候语
            greeting = config.get("greeting", "你好")
            
            # 添加问候消息
            greeting_message = HumanMessage(content=f"{greeting}！这是一个自定义节点的问候。")
            state.add_message(greeting_message)
            
            return NodeExecutionResult(
                state=state,
                next_node=config.get("next_node")
            )
        
        def get_config_schema(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "greeting": {
                        "type": "string",
                        "description": "问候语"
                    },
                    "next_node": {
                        "type": "string",
                        "description": "下一个节点"
                    }
                }
            }
    
    # 创建临时工作流配置
    import yaml
    import tempfile
    
    config_data = {
        "name": "custom_node_workflow",
        "description": "自定义节点演示工作流",
        "nodes": {
            "greeting": {
                "type": "custom_greeting_node",
                "config": {
                    "greeting": "欢迎使用工作流系统",
                    "next_node": "final"
                }
            },
            "final": {
                "type": "llm_node",
                "config": {
                    "llm_client": "mock_client",
                    "system_prompt": "你是一个友好的助手，请对用户的问候进行回应。"
                }
            }
        },
        "edges": [
            {
                "from": "greeting",
                "to": "final",
                "type": "simple"
            }
        ],
        "entry_point": "greeting"
    }
    
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name
    
    try:
        # 创建工作流管理器
        manager = WorkflowManager()
        
        print(f"\n注册自定义节点: custom_greeting_node")
        print(f"✓ 自定义节点注册成功")
        
        print(f"\n加载包含自定义节点的工作流...")
        workflow_id = manager.load_workflow(temp_path)
        print(f"✓ 工作流加载成功，ID: {workflow_id}")
        
        # 运行工作流
        print(f"\n运行工作流...")
        initial_state = AgentState()
        result = manager.run_workflow(workflow_id, initial_state)
        
        print(f"✓ 工作流执行完成")
        
        # 处理不同类型的结果
        if isinstance(result, dict):
            messages = result.get('messages', [])
        else:
            messages = result.messages
        
        print(f"  - 最终消息数: {len(messages)}")
        
        # 显示消息内容
        for i, message in enumerate(messages):
            if hasattr(message, 'content'):
                print(f" 消息 {i+1}: {message.content}") # type: ignore
        
    except Exception as e:
        print(f"✗ 演示失败: {e}")
    
    finally:
        # 清理临时文件
        Path(temp_path).unlink()


def main() -> None:
    """主函数"""
    print("工作流系统演示")
    print("基于LangGraph的YAML配置化工作流系统")
    
    try:
        # 演示基本工作流
        demo_basic_workflow()
        
        # 演示Plan-and-Execute工作流
        demo_plan_execute_workflow()
        
        # 演示自定义节点
        demo_custom_node()
        
        print("\n" + "=" * 60)
        print("演示完成！")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n演示被用户中断")
    except Exception as e:
        print(f"\n演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()



if __name__ == "__main__":
    main()