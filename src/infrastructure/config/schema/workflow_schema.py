"""Workflow配置模式

定义Workflow模块的配置验证模式，与配置加载模块集成。
"""

from typing import Dict, Any, List, Optional
import logging

from .base_schema import BaseSchema
from src.infrastructure.validation.result import ValidationResult
from src.interfaces.config import IConfigLoader

logger = logging.getLogger(__name__)


class WorkflowSchema(BaseSchema):
    """Workflow配置模式
    
    定义Workflow模块的配置验证规则和模式，与配置加载模块集成。
    """
    
    def __init__(self, config_loader: Optional[IConfigLoader] = None):
        """初始化Workflow配置模式
        
        Args:
            config_loader: 配置加载器，用于动态加载配置模式
        """
        super().__init__()
        self.config_loader = config_loader
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        logger.debug("Workflow配置模式初始化完成")
    
    def get_schema_definition(self) -> Dict[str, Any]:
        """获取模式定义
        
        Returns:
            模式定义字典
        """
        # 尝试从缓存获取
        if "workflow_config" in self._schema_cache:
            return self._schema_cache["workflow_config"]
        
        # 尝试从配置文件加载
        schema = self._load_schema_from_config("workflow_config")
        
        if schema is None:
            # 如果无法从配置加载，使用基础模式
            schema = self._get_base_workflow_config_schema()
        
        # 缓存模式
        self._schema_cache["workflow_config"] = schema
        return schema
    
    def _load_schema_from_config(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """从配置文件加载模式
        
        Args:
            schema_name: 模式名称
            
        Returns:
            模式字典或None
        """
        if not self.config_loader:
            return None
        
        try:
            # 尝试加载模式配置文件
            schema_path = f"config/schema/workflow/{schema_name}"
            schema_config = self.config_loader.load(schema_path)
            
            if schema_config and "schema" in schema_config:
                logger.debug(f"从配置文件加载模式: {schema_name}")
                return schema_config["schema"]
            
        except Exception as e:
            logger.debug(f"无法从配置文件加载模式 {schema_name}: {e}")
        
        return None
    
    def _get_base_workflow_config_schema(self) -> Dict[str, Any]:
        """获取基础Workflow配置模式
        
        Returns:
            基础Workflow配置模式字典
        """
        return {
            "type": "object",
            "required": ["workflow_name", "nodes"],
            "properties": {
                "workflow_name": {
                    "type": "string",
                    "description": "工作流名称"
                },
                "description": {
                    "type": "string",
                    "description": "工作流描述"
                },
                "workflow_type": {
                    "type": "string",
                    "description": "工作流类型"
                },
                "nodes": {
                    "type": "object",
                    "description": "节点配置"
                },
                "edges": {
                    "type": "array",
                    "description": "边配置"
                }
            }
        }
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        # 基础验证
        base_result = super().validate(config)
        errors.extend(base_result.errors)
        warnings.extend(base_result.warnings)
        
        # Workflow特定验证
        errors.extend(self._validate_workflow_structure(config))
        errors.extend(self._validate_nodes(config))
        errors.extend(self._validate_edges(config))
        errors.extend(self._validate_state_schema(config))
        
        # 生成警告
        warnings.extend(self._generate_warnings(config))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_workflow_structure(self, config: Dict[str, Any]) -> List[str]:
        """验证工作流结构
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        
        # 验证工作流名称
        workflow_name = config.get("workflow_name")
        if not workflow_name:
            errors.append("工作流名称不能为空")
        elif not isinstance(workflow_name, str):
            errors.append("工作流名称必须是字符串")
        
        # 验证工作流类型
        workflow_type = config.get("workflow_type")
        if workflow_type:
            # 从模式定义获取有效类型
            schema = self.get_schema_definition()
            workflow_type_schema = schema.get("properties", {}).get("workflow_type", {})
            valid_types = workflow_type_schema.get("enum", [])
            
            if valid_types and workflow_type not in valid_types:
                errors.append(f"不支持的工作流类型: {workflow_type}")
        
        # 验证数值字段
        numeric_fields = self._get_numeric_field_ranges()
        
        for field_name, (min_val, max_val) in numeric_fields.items():
            if field_name in config:
                value = config[field_name]
                if not isinstance(value, (int, float)):
                    errors.append(f"{field_name}必须是数字类型")
                elif min_val is not None and value < min_val:
                    errors.append(f"{field_name}必须大于等于{min_val}")
                elif max_val is not None and value > max_val:
                    errors.append(f"{field_name}必须小于等于{max_val}")
        
        return errors
    
    def _validate_nodes(self, config: Dict[str, Any]) -> List[str]:
        """验证节点配置
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        nodes = config.get("nodes", {})
        
        if not nodes:
            errors.append("至少需要配置一个节点")
            return errors
        
        for node_name, node_config in nodes.items():
            if not isinstance(node_config, dict):
                errors.append(f"节点 {node_name} 配置必须是字典")
                continue
            
            # 验证函数配置
            if "function" not in node_config:
                errors.append(f"节点 {node_name} 缺少function配置")
            
            # 验证节点配置
            node_config_dict = node_config.get("config", {})
            if not isinstance(node_config_dict, dict):
                errors.append(f"节点 {node_name} 的config配置必须是字典")
        
        return errors
    
    def _validate_edges(self, config: Dict[str, Any]) -> List[str]:
        """验证边配置
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        edges = config.get("edges", [])
        nodes = set(config.get("nodes", {}).keys())
        
        for i, edge in enumerate(edges):
            if not isinstance(edge, dict):
                errors.append(f"边 {i} 配置必须是字典")
                continue
            
            # 验证起始节点
            from_node = edge.get("from")
            if not from_node:
                errors.append(f"边 {i} 缺少from配置")
            elif from_node not in nodes and from_node != "__start__":
                errors.append(f"边 {i} 引用了不存在的起始节点: {from_node}")
            
            # 验证目标节点
            to_node = edge.get("to")
            edge_type = edge.get("type", "simple")
            if edge_type == "simple" and not to_node:
                errors.append(f"简单边 {i} 必须指定to配置")
            elif to_node and to_node not in nodes and to_node != "__end__":
                errors.append(f"边 {i} 引用了不存在的目标节点: {to_node}")
            
            # 验证边类型
            schema = self.get_schema_definition()
            edges_schema = schema.get("properties", {}).get("edges", {})
            items_schema = edges_schema.get("items", {})
            edge_type_schema = items_schema.get("properties", {}).get("type", {})
            valid_edge_types = edge_type_schema.get("enum", [])
            
            if valid_edge_types and edge_type not in valid_edge_types:
                errors.append(f"边 {i} 类型不支持: {edge_type}")
            
            # 验证条件边
            if edge_type == "conditional":
                if "condition" not in edge and "path_map" not in edge:
                    errors.append(f"条件边 {i} 必须指定condition或path_map")
        
        return errors
    
    def _validate_state_schema(self, config: Dict[str, Any]) -> List[str]:
        """验证状态模式
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        state_schema = config.get("state_schema", {})
        
        if not state_schema:
            return errors
        
        # 验证状态名称
        if "name" not in state_schema:
            errors.append("状态模式必须指定name")
        
        # 验证字段配置
        fields = state_schema.get("fields", {})
        if not fields:
            errors.append("状态模式必须包含字段定义")
            return errors
        
        for field_name, field_config in fields.items():
            if not isinstance(field_config, dict):
                errors.append(f"状态字段 {field_name} 配置必须是字典")
                continue
            
            if "type" not in field_config:
                errors.append(f"状态字段 {field_name} 必须指定type")
        
        return errors
    
    def _generate_warnings(self, config: Dict[str, Any]) -> List[str]:
        """生成警告
        
        Args:
            config: 配置数据
            
        Returns:
            警告列表
        """
        warnings = []
        
        # 检查是否缺少描述
        if not config.get("description"):
            warnings.append("建议添加工作流描述")
        
        # 检查是否缺少入口点
        if not config.get("entry_point"):
            warnings.append("建议指定入口点")
        
        # 检查是否缺少元数据
        metadata = config.get("metadata", {})
        if not metadata.get("version"):
            warnings.append("建议在元数据中指定版本")
        
        # 检查重试配置
        retry_attempts = config.get("retry_attempts", 0)
        if retry_attempts > 5:
            warnings.append("重试次数过多可能影响性能")
        
        return warnings
    
    def _get_numeric_field_ranges(self) -> Dict[str, tuple]:
        """获取数值字段的范围
        
        Returns:
            字段名到范围元组的映射
        """
        # 默认范围
        default_ranges = {
            "max_iterations": (1, 1000),
            "timeout": (1, None),
            "retry_attempts": (0, None),
            "retry_delay": (0, None)
        }
        
        # 尝试从模式定义获取范围
        try:
            schema = self.get_schema_definition()
            ranges = {}
            
            properties = schema.get("properties", {})
            for field_name, field_schema in properties.items():
                if field_schema.get("type") in ["integer", "number"]:
                    min_val = field_schema.get("minimum")
                    max_val = field_schema.get("maximum")
                    if min_val is not None or max_val is not None:
                        ranges[field_name] = (min_val, max_val)
            
            # 检查嵌套的数值字段
            nodes_schema = properties.get("nodes", {})
            pattern_properties = nodes_schema.get("patternProperties", {})
            
            if pattern_properties:
                # 获取第一个模式（所有节点共享）
                for pattern_schema in pattern_properties.values():
                    node_properties = pattern_schema.get("properties", {})
                    config_schema = node_properties.get("config", {})
                    config_properties = config_schema.get("properties", {})
                    
                    for field_name, field_schema in config_properties.items():
                        if field_schema.get("type") in ["integer", "number"]:
                            min_val = field_schema.get("minimum")
                            max_val = field_schema.get("maximum")
                            if min_val is not None or max_val is not None:
                                ranges[f"node.{field_name}"] = (min_val, max_val)
                    break
            
            # 如果从模式获取到了范围，使用它们；否则使用默认范围
            return ranges if ranges else default_ranges
            
        except Exception as e:
            logger.debug(f"获取数值字段范围失败: {e}")
            return default_ranges