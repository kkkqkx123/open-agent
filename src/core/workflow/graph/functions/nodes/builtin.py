"""Core层节点函数实现

提供符合INodeFunction接口的节点函数实现，直接在Core层实现业务逻辑。
"""

from typing import Dict, Any

from src.interfaces.workflow.functions import INodeFunction, FunctionType, FunctionMetadata
from src.interfaces.state.workflow import IWorkflowState


class LLMNodeFunction(INodeFunction):
    """LLM节点函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="node:llm",
            name="llm_node",
            function_type=FunctionType.NODE,
            description="执行LLM推理的节点函数",
            category="builtin",
            is_async=True
        )
        self._initialized = False
    
    @property
    def function_id(self) -> str:
        return self._metadata.function_id
    
    @property
    def name(self) -> str:
        return self._metadata.name
    
    @property
    def description(self) -> str:
        return self._metadata.description
    
    @property
    def version(self) -> str:
        return self._metadata.version
    
    @property
    def function_type(self) -> FunctionType:
        return self._metadata.function_type
    
    @property
    def is_async(self) -> bool:
        return self._metadata.is_async
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "state": {
                "type": "IWorkflowState",
                "required": True,
                "description": "当前工作流状态"
            },
            "config": {
                "type": "Dict[str, Any]",
                "required": True,
                "description": "节点配置，包含prompt、model等",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "Any"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化LLM节点函数"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理LLM节点函数资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证节点配置"""
        errors = []
        
        if not config.get("prompt"):
            errors.append("prompt是必需的")
        
        if not config.get("model"):
            errors.append("model是必需的")
        
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        if "config" not in params:
            errors.append("config参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    async def execute(self, state: IWorkflowState, config: Dict[str, Any]) -> Any:
        """执行节点函数
        
        Args:
            state: 工作流状态
            config: 节点配置
            
        Returns:
            Any: 执行结果
        """
        # 这里应该调用实际的LLM服务
        # 为了演示，返回模拟结果
        prompt = config.get("prompt", "")
        model = config.get("model", "default")
        
        # 模拟LLM调用
        result = {
            "content": f"LLM响应：基于prompt '{prompt}' 使用模型 {model}",
            "model": model,
            "tokens_used": 100,
            "execution_time": 0.5
        }
        
        # 更新状态
        messages = state.get("messages", [])
        messages.append({
            "role": "assistant",
            "content": result["content"],
            "model": model,
            "tokens_used": result["tokens_used"]
        })
        state["messages"] = messages
        
        return result


class ToolCallNodeFunction(INodeFunction):
    """工具调用节点函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="node:tool_call",
            name="tool_call_node",
            function_type=FunctionType.NODE,
            description="执行工具调用的节点函数",
            category="builtin",
            is_async=True
        )
        self._initialized = False
    
    @property
    def function_id(self) -> str:
        return self._metadata.function_id
    
    @property
    def name(self) -> str:
        return self._metadata.name
    
    @property
    def description(self) -> str:
        return self._metadata.description
    
    @property
    def version(self) -> str:
        return self._metadata.version
    
    @property
    def function_type(self) -> FunctionType:
        return self._metadata.function_type
    
    @property
    def is_async(self) -> bool:
        return self._metadata.is_async
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "state": {
                "type": "IWorkflowState",
                "required": True,
                "description": "当前工作流状态"
            },
            "config": {
                "type": "Dict[str, Any]",
                "required": True,
                "description": "节点配置，包含tool_name、tool_args等",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "Any"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化工具调用节点函数"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理工具调用节点函数资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证节点配置"""
        errors = []
        
        if not config.get("tool_name"):
            errors.append("tool_name是必需的")
        
        if not config.get("tool_args"):
            errors.append("tool_args是必需的")
        
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        if "config" not in params:
            errors.append("config参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    async def execute(self, state: IWorkflowState, config: Dict[str, Any]) -> Any:
        """执行节点函数
        
        Args:
            state: 工作流状态
            config: 节点配置
            
        Returns:
            Any: 执行结果
        """
        # 这里应该调用实际的工具服务
        # 为了演示，返回模拟结果
        tool_name = config.get("tool_name", "")
        tool_args = config.get("tool_args", {})
        
        # 模拟工具调用
        result = {
            "tool_name": tool_name,
            "tool_args": tool_args,
            "result": f"工具 {tool_name} 的执行结果",
            "success": True,
            "execution_time": 0.3
        }
        
        # 更新状态
        tool_results = state.get("tool_results", [])
        tool_results.append(result)
        state["tool_results"] = tool_results
        
        return result


class ConditionCheckNodeFunction(INodeFunction):
    """条件检查节点函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="node:condition_check",
            name="condition_check_node",
            function_type=FunctionType.NODE,
            description="执行条件检查的节点函数",
            category="builtin",
            is_async=False
        )
        self._initialized = False
    
    @property
    def function_id(self) -> str:
        return self._metadata.function_id
    
    @property
    def name(self) -> str:
        return self._metadata.name
    
    @property
    def description(self) -> str:
        return self._metadata.description
    
    @property
    def version(self) -> str:
        return self._metadata.version
    
    @property
    def function_type(self) -> FunctionType:
        return self._metadata.function_type
    
    @property
    def is_async(self) -> bool:
        return self._metadata.is_async
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "state": {
                "type": "IWorkflowState",
                "required": True,
                "description": "当前工作流状态"
            },
            "config": {
                "type": "Dict[str, Any]",
                "required": True,
                "description": "节点配置，包含condition等",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "Any"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化条件检查节点函数"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理条件检查节点函数资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证节点配置"""
        errors = []
        
        if not config.get("condition"):
            errors.append("condition是必需的")
        
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        if "config" not in params:
            errors.append("config参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    async def execute(self, state: IWorkflowState, config: Dict[str, Any]) -> Any:
        """执行节点函数
        
        Args:
            state: 工作流状态
            config: 节点配置
            
        Returns:
            Any: 执行结果
        """
        condition = config.get("condition", "")
        
        # 模拟条件检查
        try:
            # 创建安全的执行环境
            safe_globals = {
                "__builtins__": {
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "any": any,
                    "all": all,
                    "abs": abs,
                    "min": min,
                    "max": max,
                    "sum": sum,
                },
                "state": state,
            }
            
            # 执行条件表达式
            result = eval(condition, safe_globals)
            
            return {
                "condition": condition,
                "result": bool(result),
                "success": True
            }
            
        except Exception as e:
            return {
                "condition": condition,
                "result": False,
                "success": False,
                "error": str(e)
            }


class DataTransformNodeFunction(INodeFunction):
    """数据转换节点函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="node:data_transform",
            name="data_transform_node",
            function_type=FunctionType.NODE,
            description="执行数据转换的节点函数",
            category="builtin",
            is_async=False
        )
        self._initialized = False
    
    @property
    def function_id(self) -> str:
        return self._metadata.function_id
    
    @property
    def name(self) -> str:
        return self._metadata.name
    
    @property
    def description(self) -> str:
        return self._metadata.description
    
    @property
    def version(self) -> str:
        return self._metadata.version
    
    @property
    def function_type(self) -> FunctionType:
        return self._metadata.function_type
    
    @property
    def is_async(self) -> bool:
        return self._metadata.is_async
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "state": {
                "type": "IWorkflowState",
                "required": True,
                "description": "当前工作流状态"
            },
            "config": {
                "type": "Dict[str, Any]",
                "required": True,
                "description": "节点配置，包含transform_type等",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "Any"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化数据转换节点函数"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理数据转换节点函数资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证节点配置"""
        errors = []
        
        if not config.get("transform_type"):
            errors.append("transform_type是必需的")
        
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        if "config" not in params:
            errors.append("config参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    async def execute(self, state: IWorkflowState, config: Dict[str, Any]) -> Any:
        """执行节点函数
        
        Args:
            state: 工作流状态
            config: 节点配置
            
        Returns:
            Any: 执行结果
        """
        transform_type = config.get("transform_type", "")
        source_key = config.get("source_key", "data")
        target_key = config.get("target_key", "transformed_data")
        
        # 获取源数据
        source_data = state.get(source_key, {})
        
        # 模拟数据转换
        if transform_type == "flatten":
            # 扁平化数据
            result = {}
            def flatten_dict(d, parent_key='', sep='_'):
                items = []
                for k, v in d.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten_dict(v, new_key, sep=sep).items())
                    else:
                        items.append((new_key, v))
                return dict(items)
            
            transformed = flatten_dict(source_data)
            
        elif transform_type == "filter":
            # 过滤数据
            filter_key = config.get("filter_key", "active")
            filter_value = config.get("filter_value", True)
            
            if isinstance(source_data, list):
                transformed = [item for item in source_data if item.get(filter_key) == filter_value]
            else:
                transformed = source_data
                
        elif transform_type == "aggregate":
            # 聚合数据
            aggregate_key = config.get("aggregate_key", "count")
            transformed = {
                aggregate_key: len(source_data) if isinstance(source_data, (list, dict)) else 1
            }
            
        else:
            # 默认不转换
            transformed = source_data
        
        # 更新状态
        state[target_key] = transformed
        
        return {
            "transform_type": transform_type,
            "source_key": source_key,
            "target_key": target_key,
            "result": transformed,
            "success": True
        }


class BuiltinNodeFunctions:
    """内置节点函数集合"""
    
    @staticmethod
    def get_all_functions():
        """获取所有内置节点函数"""
        return [
            LLMNodeFunction(),
            ToolCallNodeFunction(),
            ConditionCheckNodeFunction(),
            DataTransformNodeFunction(),
        ]
    
    @staticmethod
    def get_function_by_name(name: str):
        """根据名称获取节点函数"""
        functions = {
            "llm": LLMNodeFunction,
            "tool_call": ToolCallNodeFunction,
            "condition_check": ConditionCheckNodeFunction,
            "data_transform": DataTransformNodeFunction,
        }
        
        function_class = functions.get(name)
        return function_class() if function_class else None