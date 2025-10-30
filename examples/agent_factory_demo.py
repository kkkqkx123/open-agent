"""AgentFactory使用示例

演示如何使用新的AgentFactory创建和管理Agent实例。
"""

import asyncio
from unittest.mock import Mock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.domain.agent.factory import AgentFactory, set_global_factory
from src.domain.agent.config import AgentConfig
from src.infrastructure.graph.state import WorkflowState, BaseMessage, MessageRole
from src.infrastructure.llm.interfaces import ILLMClient
from src.infrastructure.tools.manager import IToolManager
from src.domain.tools.interfaces import IToolExecutor, ToolResult


class MockLLMClient:
    """模拟LLM客户端"""
    
    async def generate_async(self, messages):
        """模拟生成响应"""
        class MockResponse:
            content = "这是一个模拟的LLM响应"
        return MockResponse()


class MockToolManager(IToolManager, IToolExecutor):
    """模拟工具管理器"""

    def __init__(self):
        self.tools = {
            "calculator": {"name": "calculator", "description": "计算器工具"},
            "search": {"name": "search", "description": "搜索工具"}
        }

    def load_tools(self):
        """加载工具"""
        return []

    def get_tool(self, name: str):
        """获取工具"""
        raise ValueError(f"Tool {name} not found")

    def get_tool_set(self, name: str):
        """获取工具集"""
        return []

    def register_tool(self, tool):
        """注册工具"""
        pass

    def list_tools(self):
        """列出工具"""
        return list(self.tools.keys())

    def list_tool_sets(self):
        """列出工具集"""
        return []

    def reload_tools(self):
        """重新加载工具"""
        return self.load_tools()

    def execute(self, tool_call):
        """同步执行工具"""
        return ToolResult(
            tool_name=tool_call.name,
            success=True,
            output=f"工具 {tool_call.name} 执行成功",
            error=None
        )

    async def execute_async(self, tool_call):
        """异步执行工具"""
        return ToolResult(
            tool_name=tool_call.name,
            success=True,
            output=f"工具 {tool_call.name} 执行成功",
            error=None
        )

    def execute_parallel(self, tool_calls):
        """并行执行工具"""
        return [self.execute(tc) for tc in tool_calls]

    async def execute_parallel_async(self, tool_calls):
        """异步并行执行工具"""
        results = []
        for tc in tool_calls:
            results.append(await self.execute_async(tc))
        return results


async def demo_agent_factory():
    """演示AgentFactory的使用"""
    print("=== AgentFactory使用演示 ===\n")
    
    # 1. 创建模拟的依赖
    mock_llm_factory = Mock()
    mock_llm_factory.create_client.return_value = MockLLMClient()
    
    mock_tool_manager = MockToolManager()
    
    # 2. 创建AgentFactory
    agent_factory = AgentFactory(mock_llm_factory, mock_tool_manager)
    
    # 设置为全局工厂
    set_global_factory(agent_factory)
    
    print("✓ AgentFactory创建成功")
    print(f"✓ 支持的Agent类型: {agent_factory.get_supported_types()}")
    print()
    
    # 3. 创建ReAct Agent
    react_config = {
        "agent_type": "react",
        "name": "demo_react_agent",
        "description": "演示用的ReAct Agent",
        "llm": "gpt-4",
        "tools": ["calculator", "search"],
        "system_prompt": "你是一个有用的助手，可以使用工具来帮助用户。",
        "max_iterations": 5
    }
    
    print("创建ReAct Agent...")
    react_agent = agent_factory.create_agent(react_config)
    
    capabilities = react_agent.get_capabilities()
    print(f"✓ Agent创建成功: {capabilities.get('name', 'Unknown')}")
    print(f"✓ Agent类型: {capabilities.get('type', 'Unknown')}")
    print(f"✓ 可用工具: {react_agent.get_available_tools()}")
    print(f"✓ Agent能力: {capabilities}")
    print()
    
    # 4. 创建测试状态
    from src.infrastructure.graph.state import create_message
    state = WorkflowState(
        workflow_id="demo_workflow",
        messages=[create_message("请计算 2 + 3 等于多少？", MessageRole.HUMAN)],
        input="请计算 2 + 3 等于多少？",
        max_iterations=5,
        iteration_count=0,
        tool_calls=[],
        tool_results=[],
        errors=[],
        complete=False,
        metadata={}
    )

    print("执行Agent...")
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    print(f"输入消息: {last_message.content if last_message else 'None'}")
    print()
    
    # 5. 执行Agent
    try:
        result = await react_agent.execute(state, {})
        
        print("✓ Agent执行成功")
        print(f"迭代次数: {result.iteration_count}")
        print(f"工具结果数量: {len(result.tool_results)}")
        
        if result.memory:
            print("思考过程:")
            for i, memory in enumerate(result.memory[-3:], 1):  # 显示最后3条记忆
                print(f"  {i}. {memory.content}")
        
    except Exception as e:
        print(f"✗ Agent执行失败: {e}")
    
    print()
    
    # 6. 演示AgentFactory的其他功能
    print("=== AgentFactory其他功能演示 ===")
    
    # 注册自定义Agent类型
    from src.domain.agent.interfaces import IAgent
    
    class CustomAgent(IAgent):
        def __init__(self, config, llm_client, tool_executor, event_manager=None):
            self.config = config
            self.llm_client = llm_client
            self.tool_executor = tool_executor
            self.event_manager = event_manager
        
        async def execute(self, state, config):
            print(f"自定义Agent {self.config.name} 正在执行...")
            return state
        
        def get_capabilities(self):
            return {"type": "custom", "name": self.config.name}
        
        def validate_state(self, state):
            return True
        
        def can_handle(self, state):
            return True
        
        def get_available_tools(self):
            return []
    
    # 注册自定义Agent类型
    agent_factory.register_agent_type("custom", CustomAgent)
    print(f"✓ 注册自定义Agent类型成功")
    print(f"✓ 当前支持的类型: {agent_factory.get_supported_types()}")
    
    # 创建自定义Agent
    custom_config = {
        "agent_type": "custom",
        "name": "demo_custom_agent",
        "description": "演示用的自定义Agent"
    }
    
    custom_agent = agent_factory.create_agent(custom_config)
    custom_capabilities = custom_agent.get_capabilities()
    print(f"✓ 自定义Agent创建成功: {custom_capabilities.get('name', 'Unknown')}")
    
    # 执行自定义Agent
    empty_state = WorkflowState(
        workflow_id="custom_demo",
        messages=[],
        input="",
        max_iterations=5,
        iteration_count=0,
        tool_calls=[],
        tool_results=[],
        errors=[],
        complete=False,
        metadata={}
    )
    await custom_agent.execute(empty_state, {})
    
    print()
    print("=== 演示完成 ===")


if __name__ == "__main__":
    asyncio.run(demo_agent_factory())