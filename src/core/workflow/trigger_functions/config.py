"""触发器函数配置系统

定义触发器函数的配置结构。
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import yaml


@dataclass
class TriggerFunctionConfig:
    """触发器函数配置"""
    name: str
    description: str
    function_type: str  # "evaluate", "execute", "condition", "custom" 等
    parameters: Dict[str, Any]
    implementation: str  # "rest", "config", "custom.module.path"
    metadata: Dict[str, Any]
    dependencies: List[str]  # 依赖的其他函数或工具
    return_schema: Dict[str, Any]  # 返回值结构定义
    input_schema: Dict[str, Any]  # 输入参数结构定义


@dataclass
class TriggerCompositionConfig:
    """触发器组合配置 - 定义触发器的函数组合"""
    name: str
    description: str
    evaluate_function: TriggerFunctionConfig  # 评估函数配置
    execute_function: TriggerFunctionConfig   # 执行函数配置
    trigger_type: str  # "time", "state", "event", "custom"
    default_config: Dict[str, Any]  # 默认触发器配置
    metadata: Dict[str, Any]


class TriggerFunctionConfigLoader:
    """触发器函数配置加载器"""
    
    @staticmethod
    def load_from_file(file_path: str, config_manager: Optional[Any] = None) -> TriggerCompositionConfig:
        """从文件加载触发器组合配置
        
        Args:
            file_path: 配置文件路径
            config_manager: 配置管理器，如果为None则直接读取文件
            
        Returns:
            TriggerCompositionConfig: 触发器组合配置
        """
        if config_manager:
            # 使用统一配置管理器加载
            data = config_manager.load_config_for_module(file_path, "workflow")
        else:
            # 直接读取文件（向后兼容）
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        
        return TriggerFunctionConfigLoader.from_dict(data)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> TriggerCompositionConfig:
        """从字典创建触发器组合配置
        
        Args:
            data: 配置数据字典
            
        Returns:
            TriggerCompositionConfig: 触发器组合配置
        """
        # 创建评估函数配置
        eval_data = data.get("evaluate_function", {})
        evaluate_function = TriggerFunctionConfig(
            name=eval_data.get("name", "evaluate"),
            description=eval_data.get("description", ""),
            function_type=eval_data.get("function_type", "evaluate"),
            parameters=eval_data.get("parameters", {}),
            implementation=eval_data.get("implementation", "rest"),
            metadata=eval_data.get("metadata", {}),
            dependencies=eval_data.get("dependencies", []),
            return_schema=eval_data.get("return_schema", {}),
            input_schema=eval_data.get("input_schema", {})
        )
        
        # 创建执行函数配置
        exec_data = data.get("execute_function", {})
        execute_function = TriggerFunctionConfig(
            name=exec_data.get("name", "execute"),
            description=exec_data.get("description", ""),
            function_type=exec_data.get("function_type", "execute"),
            parameters=exec_data.get("parameters", {}),
            implementation=exec_data.get("implementation", "rest"),
            metadata=exec_data.get("metadata", {}),
            dependencies=exec_data.get("dependencies", []),
            return_schema=exec_data.get("return_schema", {}),
            input_schema=exec_data.get("input_schema", {})
        )
        
        return TriggerCompositionConfig(
            name=data["name"],
            description=data.get("description", ""),
            evaluate_function=evaluate_function,
            execute_function=execute_function,
            trigger_type=data.get("trigger_type", "custom"),
            default_config=data.get("default_config", {}),
            metadata=data.get("metadata", {})
        )