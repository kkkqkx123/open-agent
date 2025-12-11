"""工具执行节点

负责执行工具调用并处理结果。
"""

from typing import Dict, Any, Optional, List
import time
from src.interfaces.dependency_injection import get_logger

from src.core.workflow.graph.decorators import node
from src.infrastructure.graph.nodes import SyncNode
from src.interfaces.workflow.graph import NodeExecutionResult
from src.interfaces.state.base import IState
from src.interfaces.tool.base import IToolRegistry, ToolCall, ToolResult
# TODO: 修复 node_config_loader 模块缺失问题
# from src.core.workflow.config.node_config_loader import get_node_config_loader

logger = get_logger(__name__)


@node("tool_node")
class ToolNode(SyncNode):
    """工具执行节点
    
    这是一个纯同步节点，用于协调工具执行。
    工具本身可能是同步或异步的，但节点层面是同步协调。
    
    特点：
    - execute() 有真实的同步实现，协调工具执行
    - execute_async() 抛出RuntimeError（不支持异步）
    - 工具的异步性由工具系统内部处理
    """

    def __init__(self, tool_manager: IToolRegistry) -> None:
        """初始化工具节点

        Args:
            tool_manager: 工具管理器实例（必需）
        """
        self._tool_manager = tool_manager

    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "tool_node"

    def execute(self, state: IState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行工具调用逻辑

        Args:
            state: 当前工作流状态
            config: 节点配置

        Returns:
            NodeExecutionResult: 执行结果
        """
        # 使用BaseNode的merge_configs方法合并配置
        merged_config = self.merge_configs(config)
        
        # 使用注入的工具管理器
        tool_manager = self._tool_manager
        
        # 解析工具调用
        tool_calls = self._extract_tool_calls(state, merged_config)
        
        if not tool_calls:
            # 没有工具调用，直接返回
            return NodeExecutionResult(
                state=state,
                next_node="analysis_node",  # 返回分析节点
                metadata={"message": "没有找到工具调用"}
            )
        
        # 执行工具调用
        tool_results = []
        execution_errors = []
        
        # 确保 tool_results 列表存在
        if state.get_data("tool_results") is None:
            state.set_data("tool_results", [])
        
        for tool_call in tool_calls:
            try:
                # 设置超时
                timeout = merged_config.get("timeout", 30)
                if tool_call.timeout:
                    timeout = tool_call.timeout
                
                # 执行工具
                start_time = time.time()
                tool = tool_manager.get_tool(tool_call.name)
                if tool is None:
                    raise ValueError(f"Tool '{tool_call.name}' not found")
                result = tool.execute(**tool_call.arguments)
                execution_time = time.time() - start_time
                
                # 将结果包装为ToolResult对象
                if isinstance(result, ToolResult):
                    tool_result = result
                else:
                    # 如果返回的是字符串或其他类型，包装为ToolResult
                    tool_result = ToolResult(
                        success=True,
                        output=result,
                        error=None,
                        tool_name=tool_call.name,
                        execution_time=execution_time
                    )
                
                # 记录结果
                tool_results.append(tool_result)
                
                # 添加到状态 - 转换为字典格式
                current_tool_results = state.get_data("tool_results", [])
                current_tool_results.append({
                    "tool_name": tool_result.tool_name,
                    "success": tool_result.success,
                    "output": tool_result.output,
                    "error": tool_result.error,
                    "execution_time": tool_result.execution_time
                })
                state.set_data("tool_results", current_tool_results)
                
            except Exception as e:
                error_msg = f"工具 '{tool_call.name}' 执行失败: {str(e)}"
                execution_errors.append(error_msg)
                
                # 记录错误结果 - 转换为字典格式
                current_tool_results = state.get_data("tool_results", [])
                error_result = {
                    "tool_name": tool_call.name,
                    "success": False,
                    "output": None,
                    "error": error_msg,
                    "execution_time": 0
                }
                current_tool_results.append(error_result)
                state.set_data("tool_results", current_tool_results)

        # 确定下一步
        next_node = self._determine_next_node(tool_results, execution_errors, config)
        
        return NodeExecutionResult(
            state=state,
            next_node=next_node,
            metadata={
                "tool_calls_count": len(tool_calls),
                "successful_calls": len(tool_results),
                "failed_calls": len(execution_errors),
                "errors": execution_errors,
                "execution_time": sum(r.execution_time for r in tool_results if r.execution_time)
            }
        )

    def get_config_schema(self) -> Dict[str, Any]:
        """获取节点配置Schema"""
        try:
            from ...config.schema_generator import generate_node_schema
            return generate_node_schema("tool_node")
        except Exception as e:
            logger.warning(f"无法从配置文件生成Schema，使用默认Schema: {e}")
            return self._get_fallback_schema()
    
    def _get_fallback_schema(self) -> Dict[str, Any]:
        """获取备用Schema（当配置文件不可用时）"""
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


    def _extract_tool_calls(self, state: IState, config: Dict[str, Any]) -> List[ToolCall]:
        """从状态中提取工具调用（使用类型安全的接口）

        Args:
            state: 当前工作流状态
            config: 节点配置

        Returns:
            List[ToolCall]: 工具调用列表
        """
        tool_calls: List[ToolCall] = []
        from src.interfaces.dependency_injection import get_logger
        logger = get_logger(__name__)

        # 从最后一条消息中提取工具调用
        messages = state.get_data("messages", [])
        if messages:
            last_message = messages[-1]
            
            # 使用类型安全的接口方法
            from src.interfaces.messages import IBaseMessage
            if isinstance(last_message, IBaseMessage):
                try:
                    tool_calls_data = last_message.get_tool_calls()
                    for tool_call_data in tool_calls_data:
                        tool_call = self._convert_to_tool_call(tool_call_data, config)
                        if tool_call:
                            tool_calls.append(tool_call)
                except Exception as e:
                    logger.error(f"从接口消息提取工具调用时出错: {str(e)}")
                    # 回退到后备方案
                    tool_calls = self._fallback_tool_calls_extraction(last_message, config)
            else:
                # 对于非接口消息，使用消息转换器或后备方案
                try:
                    from src.infrastructure.messages.converters import MessageConverter
                    converter = MessageConverter()
                    base_message = converter.to_base_message(last_message)
                    tool_calls_data = base_message.get_tool_calls()
                    for tool_call_data in tool_calls_data:
                        tool_call = self._convert_to_tool_call(tool_call_data, config)
                        if tool_call:
                            tool_calls.append(tool_call)
                except Exception as e:
                    logger.error(f"转换消息并提取工具调用时出错: {str(e)}")
                    # 回退到后备方案
                    tool_calls = self._fallback_tool_calls_extraction(last_message, config)
        
        logger.debug(f"提取到 {len(tool_calls)} 个工具调用")
        return tool_calls
    
    def _convert_to_tool_call(self, tool_call_data: Dict[str, Any], config: Dict[str, Any]) -> Optional[ToolCall]:
        """将工具调用数据转换为 ToolCall 对象
        
        Args:
            tool_call_data: 工具调用数据
            config: 配置信息
            
        Returns:
            Optional[ToolCall]: 转换后的 ToolCall 对象
        """
        if not isinstance(tool_call_data, dict):
            return None
            
        # 处理标准格式
        name = tool_call_data.get("name", "")
        args = tool_call_data.get("args", {})
        call_id = tool_call_data.get("id", "")
        
        # 处理 OpenAI 格式
        if not name and "function" in tool_call_data:
            function = tool_call_data["function"]
            name = function.get("name", "")
            args_str = function.get("arguments", "{}")
            
            # 解析 JSON 参数
            import json
            try:
                args = json.loads(args_str)
            except json.JSONDecodeError:
                from src.interfaces.dependency_injection import get_logger
                logger = get_logger(__name__)
                logger.warning(f"无法解析工具参数 JSON: {args_str}")
                args = {}
        
        if name:  # 只有当工具名称不为空时才添加
            return ToolCall(
                name=name,
                arguments=args,
                call_id=call_id,
                timeout=config.get("timeout")
            )
        
        return None
    
    def _fallback_tool_calls_extraction(self, message: Any, config: Dict[str, Any]) -> List[ToolCall]:
        """后备工具调用提取（用于兼容性）
        
        Args:
            message: 消息对象
            config: 配置信息
            
        Returns:
            List[ToolCall]: 工具调用列表
        """
        tool_calls: List[ToolCall] = []
        from src.interfaces.dependency_injection import get_logger
        logger = get_logger(__name__)
        
        # 检查是否是 LangChain 消息类型
        if hasattr(message, 'has_tool_calls') and callable(message.has_tool_calls):
            try:
                if message.has_tool_calls():
                    tool_calls_data = message.get_tool_calls()
                else:
                    tool_calls_data = []
                for tool_call_data in tool_calls_data:
                    tool_call = self._convert_to_tool_call(tool_call_data, config)
                    if tool_call:
                        tool_calls.append(tool_call)
            except Exception as e:
                logger.error(f"解析 LangChain tool_calls 时出错: {str(e)}")
        
        # 检查 additional_kwargs 中的 tool_calls（OpenAI 格式）
        elif (hasattr(message, 'additional_kwargs') and
              message.additional_kwargs and
              "tool_calls" in message.additional_kwargs):
            try:
                for tool_call_data in message.additional_kwargs["tool_calls"]:
                    tool_call = self._convert_to_tool_call(tool_call_data, config)
                    if tool_call:
                        tool_calls.append(tool_call)
            except Exception as e:
                logger.error(f"解析 additional_kwargs tool_calls 时出错: {str(e)}")
        
        # 检查是否是字典格式的消息（包含 tool_calls）
        elif isinstance(message, dict) and "tool_calls" in message:
            try:
                for tool_call_data in message["tool_calls"]:
                    tool_call = self._convert_to_tool_call(tool_call_data, config)
                    if tool_call:
                        tool_calls.append(tool_call)
            except Exception as e:
                logger.error(f"解析字典格式 tool_calls 时出错: {str(e)}")
        
        # 最后尝试从文本内容中解析（非标准方式，仅作为后备）
        elif (isinstance(message, dict) and "content" in message and
              isinstance(message["content"], str) and
              message["content"].strip()):
            try:
                content = message["content"].strip()
                # 检查是否包含可能的工具调用指示
                if any(indicator in content.lower() for indicator in ["调用工具", "call tool", "tool:"]):
                    logger.warning("使用非标准的文本解析方式提取工具调用，建议使用标准格式")
                    tool_calls = self._parse_tool_calls_from_text(content)
            except Exception as e:
                logger.error(f"从文本解析工具调用时出错: {str(e)}")
        
        return tool_calls

    def _parse_tool_calls_from_text(self, content: str) -> List[ToolCall]:
        """从文本中解析工具调用（非标准方式，仅作为后备方案）

        Args:
            content: 消息内容

        Returns:
            List[ToolCall]: 工具调用列表
        """
        from src.interfaces.dependency_injection import get_logger
        import json
        import re
        logger = get_logger(__name__)
        
        tool_calls: List[ToolCall] = []
        
        # 支持多种工具调用模式
        patterns = [
            # 中文模式：调用工具:工具名(参数)
            r"调用工具[：:]\s*(\w+)\s*\((.*?)\)",
            # 英文模式：call tool:tool_name(args)
            r"call\s+tool[：:]\s*(\w+)\s*\((.*?)\)",
            # 简化模式：tool_name(args)
            r"(\w+)\s*\((.*?)\)",
            # JSON模式：{"tool": "tool_name", "args": {...}}
            r'\{\s*"tool"\s*:\s*"(\w+)"\s*,\s*"args"\s*:\s*(\{.*?\})\s*\}',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                try:
                    if len(match) == 2:
                        tool_name, args_str = match
                    elif len(match) == 1:
                        # JSON模式可能只返回一个匹配
                        continue
                    else:
                        continue
                    
                    tool_name = tool_name.strip()
                    if not tool_name:
                        continue
                    
                    # 解析参数
                    arguments = {}
                    if args_str and args_str.strip():
                        args_str = args_str.strip()
                        
                        # 尝试直接解析为JSON
                        try:
                            if args_str.startswith('{') and args_str.endswith('}'):
                                arguments = json.loads(args_str)
                            else:
                                # 尝试包装为JSON
                                arguments = json.loads(f"{{{args_str}}}")
                        except json.JSONDecodeError:
                            # 如果不是JSON，尝试解析键值对
                            try:
                                arguments = self._parse_key_value_pairs(args_str)
                            except Exception:
                                # 最后作为单个参数
                                arguments = {"input": args_str}
                    
                    # 生成唯一ID
                    import uuid
                    call_id = str(uuid.uuid4())[:8]
                    
                    tool_calls.append(ToolCall(
                        name=tool_name,
                        arguments=arguments,
                        call_id=call_id
                    ))
                    
                    logger.debug(f"从文本解析出工具调用: {tool_name}")
                    
                except Exception as e:
                    logger.warning(f"解析工具调用失败: {str(e)}")
                    continue
        
        if tool_calls:
            logger.info(f"从文本中解析出 {len(tool_calls)} 个工具调用")
        
        return tool_calls
    
    def _parse_key_value_pairs(self, args_str: str) -> Dict[str, Any]:
        """解析键值对格式的参数
        
        Args:
            args_str: 参数字符串
            
        Returns:
            Dict[str, Any]: 解析后的参数字典
        """
        import re
        
        # 从合并后的配置获取键值对解析模式
        merged_config = self.merge_configs({})
        pattern_str = merged_config.get(
            "key_value_pattern",
            r'(\w+)\s*[:=]\s*["\']?([^"\'\s,]+)["\']?'
        )
        pattern = re.compile(pattern_str)
        matches = re.findall(pattern, args_str)
        
        arguments = {}
        for key, value in matches:
            # 尝试转换为适当的类型
            if value.lower() in ('true', 'false'):
                arguments[key] = value.lower() == 'true'
            elif value.isdigit():
                arguments[key] = int(value)
            elif self._is_float(value):
                arguments[key] = float(value)
            else:
                arguments[key] = value
        
        return arguments
    
    def _is_float(self, value: str) -> bool:
        """检查字符串是否可以转换为浮点数"""
        try:
            float(value)
            return '.' in value
        except ValueError:
            return False

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
        # 使用BaseNode的merge_configs方法合并配置
        merged_config = self.merge_configs(config)
        
        # 如果有错误且配置为不继续执行，返回分析节点
        if execution_errors and not merged_config.get("continue_on_error", True):
            return "analysis_node"
        
        # 如果所有工具都成功执行，返回分析节点进行下一步分析
        if tool_results and all(result.success for result in tool_results):
            return "analysis_node"
        
        # 如果有部分失败但配置为继续，也返回分析节点
        if execution_errors and merged_config.get("continue_on_error", True):
            return "analysis_node"
        
        # 默认返回分析节点
        return "analysis_node"