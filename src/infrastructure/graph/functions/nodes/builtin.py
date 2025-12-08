"""内置节点函数实现

提供符合IFunction接口的内置节点函数实现。
"""

from typing import Dict, Any, Optional, List
from src.interfaces.workflow.functions import INodeFunction, FunctionType, FunctionMetadata
from src.interfaces.state.workflow import IWorkflowState


class LLMNodeFunction(INodeFunction):
    """LLM节点函数"""
    
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
                "required": False,
                "description": "节点配置",
                "properties": {
                    "prompt": {
                        "type": "str",
                        "description": "LLM提示词"
                    },
                    "model": {
                        "type": "str",
                        "description": "LLM模型名称"
                    },
                    "temperature": {
                        "type": "float",
                        "description": "生成温度",
                        "default": 0.7
                    }
                }
            }
        }
    
    def get_return_type(self) -> str:
        return "Any"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        errors = []
        if "prompt" in config and not config["prompt"]:
            errors.append("prompt 不能为空")
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        errors = []
        if "state" not in params:
            errors.append("缺少必需参数: state")
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    async def execute(self, state: IWorkflowState, config: Dict[str, Any]) -> Any:
        """执行LLM节点函数"""
        # 这里应该调用实际的LLM服务
        # 为了示例，我们返回一个模拟结果
        return {
            "type": "llm_response",
            "content": "这是一个模拟的LLM响应",
            "model": config.get("model", "default"),
            "timestamp": "2024-01-01T00:00:00Z"
        }


class ToolCallNodeFunction(INodeFunction):
    """工具调用节点函数"""
    
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
                "required": False,
                "description": "节点配置",
                "properties": {
                    "tool_name": {
                        "type": "str",
                        "description": "工具名称"
                    },
                    "tool_args": {
                        "type": "Dict[str, Any]",
                        "description": "工具参数"
                    }
                }
            }
        }
    
    def get_return_type(self) -> str:
        return "Any"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        errors = []
        if "tool_name" in config and not config["tool_name"]:
            errors.append("tool_name 不能为空")
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        errors = []
        if "state" not in params:
            errors.append("缺少必需参数: state")
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    async def execute(self, state: IWorkflowState, config: Dict[str, Any]) -> Any:
        """执行工具调用节点函数"""
        tool_name = config.get("tool_name", "default_tool")
        tool_args = config.get("tool_args", {})
        
        # 这里应该调用实际的工具服务
        # 为了示例，我们返回一个模拟结果
        return {
            "type": "tool_result",
            "tool_name": tool_name,
            "result": f"工具 {tool_name} 的执行结果",
            "success": True,
            "timestamp": "2024-01-01T00:00:00Z"
        }


class ConditionCheckNodeFunction(INodeFunction):
    """条件检查节点函数"""
    
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
                "required": False,
                "description": "节点配置",
                "properties": {
                    "condition_type": {
                        "type": "str",
                        "description": "条件类型"
                    },
                    "condition_params": {
                        "type": "Dict[str, Any]",
                        "description": "条件参数"
                    }
                }
            }
        }
    
    def get_return_type(self) -> str:
        return "Any"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        errors = []
        if "condition_type" in config and not config["condition_type"]:
            errors.append("condition_type 不能为空")
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        errors = []
        if "state" not in params:
            errors.append("缺少必需参数: state")
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    async def execute(self, state: IWorkflowState, config: Dict[str, Any]) -> Any:
        """执行条件检查节点函数"""
        condition_type = config.get("condition_type", "default")
        condition_params = config.get("condition_params", {})
        
        # 这里应该调用实际的条件检查服务
        # 为了示例，我们返回一个模拟结果
        return {
            "type": "condition_result",
            "condition_type": condition_type,
            "result": True,
            "message": f"条件 {condition_type} 检查通过",
            "timestamp": "2024-01-01T00:00:00Z"
        }


class DataTransformNodeFunction(INodeFunction):
    """数据转换节点函数"""
    
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
                "required": False,
                "description": "节点配置",
                "properties": {
                    "transform_type": {
                        "type": "str",
                        "description": "转换类型"
                    },
                    "source_key": {
                        "type": "str",
                        "description": "源数据键"
                    },
                    "target_key": {
                        "type": "str",
                        "description": "目标数据键"
                    }
                }
            }
        }
    
    def get_return_type(self) -> str:
        return "Any"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        errors = []
        if "transform_type" in config and not config["transform_type"]:
            errors.append("transform_type 不能为空")
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        errors = []
        if "state" not in params:
            errors.append("缺少必需参数: state")
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    async def execute(self, state: IWorkflowState, config: Dict[str, Any]) -> Any:
        """执行数据转换节点函数"""
        transform_type = config.get("transform_type", "copy")
        source_key = config.get("source_key", "data")
        target_key = config.get("target_key", "transformed_data")
        
        # 获取源数据
        source_data = state.get_data(source_key, {})
        
        # 执行转换
        if transform_type == "copy":
            transformed_data = source_data.copy()
        elif transform_type == "uppercase":
            transformed_data = str(source_data).upper()
        elif transform_type == "lowercase":
            transformed_data = str(source_data).lower()
        else:
            transformed_data = source_data
        
        # 更新状态
        state.set_data(target_key, transformed_data)
        
        return {
            "type": "transform_result",
            "transform_type": transform_type,
            "source_key": source_key,
            "target_key": target_key,
            "success": True,
            "timestamp": "2024-01-01T00:00:00Z"
        }


class BuiltinNodeFunctions:
    """内置节点函数集合"""
    
    @staticmethod
    def get_all_functions() -> Dict[str, INodeFunction]:
        """获取所有内置节点函数
        
        Returns:
            Dict[str, INodeFunction]: 节点函数字典
        """
        return {
            "llm": LLMNodeFunction(),
            "tool_call": ToolCallNodeFunction(),
            "condition_check": ConditionCheckNodeFunction(),
            "data_transform": DataTransformNodeFunction(),
        }
    
    @staticmethod
    def get_function(name: str) -> Optional[INodeFunction]:
        """获取指定的内置节点函数
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[INodeFunction]: 节点函数，如果不存在返回None
        """
        functions = BuiltinNodeFunctions.get_all_functions()
        return functions.get(name)
    
    @staticmethod
    def list_functions() -> List[str]:
        """列出所有内置节点函数名称
        
        Returns:
            List[str]: 函数名称列表
        """
        return list(BuiltinNodeFunctions.get_all_functions().keys())