"""工具执行节点

负责执行工具调用并处理结果。
"""

from typing import Dict, Any, Optional, List
import time

from ..registry import BaseNode, NodeExecutionResult, node
from src.domain.agent.state import AgentState
from src.domain.tools.interfaces import ITool, IToolRegistry, ToolCall, ToolResult
from src.infrastructure.graph.adapters import get_state_adapter, get_message_adapter


@node("tool_node")
class ToolNode(BaseNode):
    """工具执行节点"""

    def __init__(self, tool_manager: Optional[IToolRegistry] = None) -> None:
        """初始化工具节点

        Args:
            tool_manager: 工具管理器实例
        """
        self._tool_manager = tool_manager

    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "tool_node"

    def execute(self, state: AgentState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行工具调用逻辑

        Args:
            state: 当前Agent状态
            config: 节点配置

        Returns:
            NodeExecutionResult: 执行结果
        """
        # 获取工具管理器
        tool_manager = self._get_tool_manager(config)
        
        # 解析工具调用
        tool_calls = self._extract_tool_calls(state, config)
        
        if not tool_calls:
            # 没有工具调用，直接返回
            return NodeExecutionResult(
                state=state,
                next_node="analyze",  # 返回分析节点
                metadata={"message": "没有找到工具调用"}
            )
        
        # 执行工具调用
        tool_results = []
        execution_errors = []
        
        for tool_call in tool_calls:
            try:
                # 设置超时
                timeout = config.get("timeout", 30)
                if tool_call.timeout:
                    timeout = tool_call.timeout
                
                # 执行工具
                start_time = time.time()
                tool = tool_manager.get_tool(tool_call.name)
                if tool is None:
                    raise ValueError(f"Tool '{tool_call.name}' not found")
                result = tool.execute(**tool_call.arguments)
                execution_time = time.time() - start_time
                
                # 记录结果
                tool_results.append(result)
                
                # 添加到状态
                state_tool_result = ToolResult(
                    success=result.success,
                    output=result.output,
                    error=result.error,
                    tool_name=tool_call.name
                )
                state.tool_results.append(state_tool_result)
                
            except Exception as e:
                error_msg = f"工具 '{tool_call.name}' 执行失败: {str(e)}"
                execution_errors.append(error_msg)
                
                # 记录错误结果
                error_result = ToolResult(
                    success=False,
                    output=None,
                    error=error_msg,
                    tool_name=tool_call.name
                )
                state.tool_results.append(error_result)

        # 确定下一步
        next_node = self._determine_next_node(tool_results, execution_errors, config)
        
        return NodeExecutionResult(
            state,
            next_node,
            {
                "tool_calls_count": len(tool_calls),
                "successful_calls": len(tool_results),
                "failed_calls": len(execution_errors),
                "errors": execution_errors,
                "execution_time": sum(r.execution_time for r in tool_results if r.execution_time)
            }
        )

    def get_config_schema(self) -> Dict[str, Any]:
        """获取节点配置Schema"""
        return {
            "type": "object",
            "properties": {
                "tool_manager": {
                    "type": "string",
                    "description": "工具管理器配置名称"
                },
                "timeout": {
                    "type": "integer",
                    "description": "工具执行超时时间（秒）",
                    "default": 30
                },
                "max_parallel_calls": {
                    "type": "integer",
                    "description": "最大并行调用数",
                    "default": 1
                },
                "retry_on_failure": {
                    "type": "boolean",
                    "description": "失败时是否重试",
                    "default": False
                },
                "max_retries": {
                    "type": "integer",
                    "description": "最大重试次数",
                    "default": 3
                },
                "continue_on_error": {
                    "type": "boolean",
                    "description": "遇到错误时是否继续执行其他工具",
                    "default": True
                }
            },
            "required": ["tool_manager"]
        }

    def _get_tool_manager(self, config: Dict[str, Any]) -> IToolRegistry:
        """获取工具管理器

        Args:
            config: 节点配置

        Returns:
            IToolManager: 工具管理器实例
        """
        if self._tool_manager:
            return self._tool_manager
        
        # 从依赖容器获取
        # TODO: 实现完整的工具管理器注册和获取逻辑
        # try:
        #     from ...infrastructure import get_global_container
        #     container = get_global_container()
        #     return container.get(IToolManager)
        # except Exception:
        #     # 如果无法获取工具管理器，返回模拟工具管理器
        #     pass

        # 暂时直接返回模拟工具管理器
        return self._create_mock_tool_manager()

    def _create_mock_tool_manager(self) -> IToolRegistry:
        """创建模拟工具管理器"""
        from src.domain.tools.base import BaseTool
        
        class MockTool(BaseTool):
            def __init__(self, name: str):
                description = f"模拟工具 {name}"
                super().__init__(name, description, {"type": "object", "properties": {}})
            
            def execute(self, **kwargs: Any) -> Any:
                return f"模拟工具 {self.name} 的执行结果"
            
            async def execute_async(self, **kwargs: Any) -> Any:
                return f"模拟工具 {self.name} 的异步执行结果"
            
            def get_schema(self) -> Dict[str, Any]:
                return {"type": "object", "properties": {}}
        
        class MockToolManager(IToolRegistry):
            def register_tool(self, tool: "ITool") -> None:
                pass

            def get_tool(self, name: str) -> Optional["ITool"]:
                return MockTool(name)

            def list_tools(self) -> List[str]:
                return ["mock_tool"]

            def unregister_tool(self, name: str) -> bool:
                return True
            
            def list_tool_sets(self) -> List[str]:
                return []
        
        return MockToolManager()

    def _extract_tool_calls(self, state: AgentState, config: Dict[str, Any]) -> List[ToolCall]:
        """从状态中提取工具调用

        Args:
            state: 当前Agent状态
            config: 节点配置

        Returns:
            List[ToolCall]: 工具调用列表
        """
        tool_calls = []

        # 从最后一条消息中提取工具调用
        if state.messages:
            last_message = state.messages[-1]

            # 检查是否有工具调用属性
            if hasattr(last_message, 'tool_calls'):
                tool_calls_attr = getattr(last_message, 'tool_calls', None)
                if tool_calls_attr:
                    for tool_call in tool_calls_attr:
                        tool_calls.append(ToolCall(
                        name=tool_call.get("name", ""),
                        arguments=tool_call.get("arguments", {}),
                        call_id=tool_call.get("id"),
                        timeout=config.get("timeout")
                        ))

            # 检查消息内容中是否包含工具调用信息
            elif hasattr(last_message, 'content') and isinstance(getattr(last_message, 'content', ''), str):
                # 简单的文本解析（实际实现可能需要更复杂的解析逻辑）
                content = getattr(last_message, 'content', '')
                tool_calls = self._parse_tool_calls_from_text(content)
        
        return tool_calls

    def _parse_tool_calls_from_text(self, content: str) -> List[ToolCall]:
        """从文本中解析工具调用

        Args:
            content: 消息内容

        Returns:
            List[ToolCall]: 工具调用列表
        """
        # 这是一个简化的实现，实际可能需要更复杂的解析逻辑
        tool_calls = []
        
        # 示例：查找 "调用工具:工具名(参数)" 模式
        import re
        pattern = r"调用工具:(\w+)\((.*?)\)"
        matches = re.findall(pattern, content)
        
        for tool_name, args_str in matches:
            try:
                # 简单参数解析
                arguments = {}
                if args_str.strip():
                    # 尝试解析为JSON
                    import json
                    try:
                        arguments = json.loads(f"{{{args_str}}}")
                    except json.JSONDecodeError:
                        # 如果不是JSON，作为字符串参数
                        arguments = {"input": args_str}

                tool_calls.append(ToolCall(
                    name=tool_name,
                    arguments=arguments
                ))
            except Exception:
                # 解析失败，跳过
                continue
        
        return tool_calls

    def _determine_next_node(
        self, 
        tool_results: List[ToolResult], 
        execution_errors: List[str], 
        config: Dict[str, Any]
    ) -> Optional[str]:
        """确定下一个节点

        Args:
            tool_results: 工具执行结果列表
            execution_errors: 执行错误列表
            config: 节点配置

        Returns:
            Optional[str]: 下一个节点名称
        """
        # 如果有错误且配置为不继续执行，返回分析节点
        if execution_errors and not config.get("continue_on_error", True):
            return "analyze"
        
        # 如果所有工具都成功执行，返回分析节点进行下一步分析
        if tool_results and all(result.success for result in tool_results):
            return "analyze"
        
        # 如果有部分失败但配置为继续，也返回分析节点
        if execution_errors and config.get("continue_on_error", True):
            return "analyze"
        
        # 默认返回分析节点
        return "analyze"