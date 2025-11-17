"""节点函数配置系统

定义节点内部函数的配置结构。
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import yaml


@dataclass
class NodeFunctionConfig:
    """节点函数配置"""
    name: str
    description: str
    function_type: str  # "llm", "tool", "analysis", "condition", "custom" 等
    parameters: Dict[str, Any]
    implementation: str  # "rest", "config", "custom.module.path"
    metadata: Dict[str, Any]
    dependencies: List[str]  # 依赖的其他函数或工具
    return_schema: Dict[str, Any]  # 返回值结构定义
    input_schema: Dict[str, Any]  # 输入参数结构定义


@dataclass
class NodeCompositionConfig:
    """节点组合配置 - 定义节点内部的函数组合"""
    name: str
    description: str
    functions: List[NodeFunctionConfig]  # 节点内部的函数列表
    execution_order: List[str]  # 函数执行顺序
    input_mapping: Dict[str, str]  # 输入映射
    output_mapping: Dict[str, str]  # 输出映射
    error_handling: Dict[str, str]  # 错误处理配置
    metadata: Dict[str, Any]


class NodeFunctionConfigLoader:
    """节点函数配置加载器"""
    
    @staticmethod
    def load_from_file(file_path: str) -> NodeCompositionConfig:
        """从文件加载节点组合配置
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            NodeCompositionConfig: 节点组合配置
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return NodeFunctionConfigLoader.from_dict(data)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> NodeCompositionConfig:
        """从字典创建节点组合配置
        
        Args:
            data: 配置数据字典
            
        Returns:
            NodeCompositionConfig: 节点组合配置
        """
        functions_data = data.get("functions", [])
        functions = []
        
        for func_data in functions_data:
            func_config = NodeFunctionConfig(
                name=func_data["name"],
                description=func_data.get("description", ""),
                function_type=func_data.get("function_type", "custom"),
                parameters=func_data.get("parameters", {}),
                implementation=func_data.get("implementation", "rest"),
                metadata=func_data.get("metadata", {}),
                dependencies=func_data.get("dependencies", []),
                return_schema=func_data.get("return_schema", {}),
                input_schema=func_data.get("input_schema", {})
            )
            functions.append(func_config)
        
        return NodeCompositionConfig(
            name=data["name"],
            description=data.get("description", ""),
            functions=functions,
            execution_order=data.get("execution_order", [f.name for f in functions]),
            input_mapping=data.get("input_mapping", {}),
            output_mapping=data.get("output_mapping", {}),
            error_handling=data.get("error_handling", {}),
            metadata=data.get("metadata", {})
        )