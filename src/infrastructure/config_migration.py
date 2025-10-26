"""配置迁移工具

提供配置迁移功能，帮助用户从旧的配置格式迁移到新的配置格式。
"""

import os
import yaml
import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from .config_models import (
    BaseConfigModel, WorkflowConfigModel, AgentConfigModel, 
    ToolConfigModel, LLMConfigModel, GraphConfigModel,
    ConfigType, ConfigMetadata
)
from .config_inheritance import ConfigInheritanceHandler
from .exceptions import ConfigurationError


@dataclass
class MigrationResult:
    """迁移结果"""
    success: bool
    source_path: str
    target_path: str
    errors: List[str]
    warnings: List[str]
    migrated_fields: Dict[str, Any]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class ConfigMigrationTool:
    """配置迁移工具"""
    
    def __init__(self, config_loader: Optional['IConfigLoader'] = None):
        """初始化配置迁移工具
        
        Args:
            config_loader: 配置加载器（可选）
        """
        self.config_loader = config_loader
        self.inheritance_handler = ConfigInheritanceHandler(config_loader)
        self.migration_rules = self._load_migration_rules()
    
    def _load_migration_rules(self) -> Dict[str, Any]:
        """加载迁移规则
        
        Returns:
            迁移规则
        """
        return {
            "workflow": {
                "field_mappings": {
                    "name": "metadata.name",
                    "description": "metadata.description",
                    "version": "metadata.version",
                    "nodes": "nodes",
                    "edges": "edges",
                    "entry_point": "entry_point",
                    "checkpointer": "checkpointer",
                    "interrupt_before": "interrupt_before",
                    "interrupt_after": "interrupt_after",
                    "max_iterations": "max_iterations",
                    "timeout": "timeout",
                    "state_schema": "state_schema"
                },
                "default_values": {
                    "config_type": "workflow",
                    "metadata": {
                        "version": "1.0.0",
                        "author": "system"
                    },
                    "max_iterations": 10,
                    "timeout": 300
                },
                "validation_rules": {
                    "metadata.name": {"required": True, "type": "string"},
                    "entry_point": {"required": True, "type": "string"},
                    "nodes": {"required": True, "type": "dict"},
                    "edges": {"required": True, "type": "list"}
                }
            },
            "agent": {
                "field_mappings": {
                    "name": "metadata.name",
                    "description": "metadata.description",
                    "version": "metadata.version",
                    "agent_type": "agent_type",
                    "llm_config": "llm_config",
                    "tools": "tools",
                    "tool_config": "tool_config",
                    "system_prompt": "system_prompt",
                    "prompt_template": "prompt_template",
                    "max_iterations": "max_iterations",
                    "temperature": "temperature",
                    "max_tokens": "max_tokens"
                },
                "default_values": {
                    "config_type": "agent",
                    "metadata": {
                        "version": "1.0.0",
                        "author": "system"
                    },
                    "agent_type": "default",
                    "max_iterations": 10,
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            },
            "tool": {
                "field_mappings": {
                    "name": "metadata.name",
                    "description": "metadata.description",
                    "version": "metadata.version",
                    "tool_type": "tool_type",
                    "parameters": "parameters",
                    "required_parameters": "required_parameters",
                    "timeout": "timeout",
                    "retry_count": "retry_count",
                    "retry_delay": "retry_delay"
                },
                "default_values": {
                    "config_type": "tool",
                    "metadata": {
                        "version": "1.0.0",
                        "author": "system"
                    },
                    "tool_type": "function",
                    "timeout": 30,
                    "retry_count": 3,
                    "retry_delay": 1.0
                }
            },
            "llm": {
                "field_mappings": {
                    "name": "metadata.name",
                    "description": "metadata.description",
                    "version": "metadata.version",
                    "model_name": "model_name",
                    "provider": "provider",
                    "temperature": "temperature",
                    "max_tokens": "max_tokens",
                    "top_p": "top_p",
                    "frequency_penalty": "frequency_penalty",
                    "presence_penalty": "presence_penalty",
                    "api_key": "api_key",
                    "base_url": "base_url",
                    "timeout": "timeout",
                    "streaming": "streaming",
                    "batch_size": "batch_size"
                },
                "default_values": {
                    "config_type": "llm",
                    "metadata": {
                        "version": "1.0.0",
                        "author": "system"
                    },
                    "provider": "openai",
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "top_p": 1.0,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0,
                    "timeout": 30,
                    "streaming": False,
                    "batch_size": 1
                }
            },
            "graph": {
                "field_mappings": {
                    "name": "metadata.name",
                    "description": "metadata.description",
                    "version": "metadata.version",
                    "graph_name": "graph_name",
                    "state_schema": "state_schema",
                    "nodes": "nodes",
                    "edges": "edges",
                    "entry_point": "entry_point",
                    "checkpointer": "checkpointer",
                    "interrupt_before": "interrupt_before",
                    "interrupt_after": "interrupt_after"
                },
                "default_values": {
                    "config_type": "graph",
                    "metadata": {
                        "version": "1.0.0",
                        "author": "system"
                    },
                    "graph_name": "default_graph"
                }
            }
        }
    
    def migrate_config(
        self, 
        source_path: Union[str, Path], 
        target_path: Union[str, Path], 
        config_type: ConfigType,
        backup: bool = True
    ) -> MigrationResult:
        """迁移配置文件
        
        Args:
            source_path: 源配置文件路径
            target_path: 目标配置文件路径
            config_type: 配置类型
            backup: 是否创建备份
            
        Returns:
            迁移结果
        """
        source_path = Path(source_path)
        target_path = Path(target_path)
        
        errors = []
        warnings = []
        migrated_fields = {}
        
        try:
            # 创建备份
            if backup and source_path.exists():
                backup_path = source_path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml")
                backup_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
                warnings.append(f"已创建备份文件: {backup_path}")
            
            # 加载旧配置
            with open(source_path, "r", encoding="utf-8") as f:
                old_config = yaml.safe_load(f) or {}
            
            # 获取迁移规则
            rules = self.migration_rules.get(config_type.value)
            if not rules:
                errors.append(f"不支持的配置类型: {config_type}")
                return MigrationResult(
                    success=False,
                    source_path=str(source_path),
                    target_path=str(target_path),
                    errors=errors,
                    warnings=warnings,
                    migrated_fields=migrated_fields
                )
            
            # 执行迁移
            new_config = self._migrate_config_data(old_config, rules, config_type)
            
            # 验证迁移后的配置
            validation_errors = self._validate_migrated_config(new_config, rules)
            if validation_errors:
                errors.extend(validation_errors)
            
            # 保存新配置
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                yaml.dump(new_config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            migrated_fields = new_config
            
            return MigrationResult(
                success=len(errors) == 0,
                source_path=str(source_path),
                target_path=str(target_path),
                errors=errors,
                warnings=warnings,
                migrated_fields=migrated_fields
            )
            
        except Exception as e:
            errors.append(f"迁移失败: {str(e)}")
            return MigrationResult(
                success=False,
                source_path=str(source_path),
                target_path=str(target_path),
                errors=errors,
                warnings=warnings,
                migrated_fields=migrated_fields
            )
    
    def _migrate_config_data(self, old_config: Dict[str, Any], rules: Dict[str, Any], config_type: ConfigType) -> Dict[str, Any]:
        """迁移配置数据
        
        Args:
            old_config: 旧配置
            rules: 迁移规则
            config_type: 配置类型
            
        Returns:
            新配置
        """
        new_config = {}
        
        # 应用默认值
        default_values = rules.get("default_values", {})
        new_config.update(default_values)
        
        # 迁移字段
        field_mappings = rules.get("field_mappings", {})
        for old_field, new_path in field_mappings.items():
            if old_field in old_config:
                value = old_config[old_field]
                self._set_nested_value(new_config, new_path, value)
        
        # 处理额外字段（不在映射规则中的字段）
        for field, value in old_config.items():
            if field not in field_mappings and field not in ["inherits_from", "metadata"]:
                # 保留额外字段
                new_config[field] = value
        
        # 处理继承配置
        if "inherits_from" in old_config:
            new_config["inherits_from"] = old_config["inherits_from"]
        
        return new_config
    
    def _set_nested_value(self, obj: Dict[str, Any], path: str, value: Any) -> None:
        """设置嵌套字典中的值
        
        Args:
            obj: 字典对象
            path: 路径（点分隔）
            value: 要设置的值
        """
        keys = path.split(".")
        current = obj
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _validate_migrated_config(self, config: Dict[str, Any], rules: Dict[str, Any]) -> List[str]:
        """验证迁移后的配置
        
        Args:
            config: 配置数据
            rules: 迁移规则
            
        Returns:
            验证错误列表
        """
        errors = []
        
        # 获取验证规则
        validation_rules = rules.get("validation_rules", {})
        
        for field_path, rule in validation_rules.items():
            value = self._get_nested_value(config, field_path)
            
            if rule.get("required") and value is None:
                errors.append(f"缺少必要字段: {field_path}")
            
            if "type" in rule and value is not None:
                expected_type = rule["type"]
                if not self._check_type(value, expected_type):
                    errors.append(f"字段 '{field_path}' 类型错误，期望 {expected_type}，实际 {type(value)}")
        
        return errors
    
    def _get_nested_value(self, obj: Dict[str, Any], path: str) -> Any:
        """获取嵌套字典中的值
        
        Args:
            obj: 字典对象
            path: 路径（点分隔）
            
        Returns:
            对应的值
        """
        keys = path.split(".")
        current = obj
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查值的类型
        
        Args:
            value: 要检查的值
            expected_type: 期望的类型字符串
            
        Returns:
            类型是否匹配
        """
        type_mapping = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "any": object
        }
        
        expected_python_type = type_mapping.get(expected_type.lower())
        if expected_python_type is None:
            return True
        
        return isinstance(value, expected_python_type)
    
    def batch_migrate_configs(
        self, 
        source_dir: Union[str, Path], 
        target_dir: Union[str, Path], 
        config_type: ConfigType,
        backup: bool = True
    ) -> List[MigrationResult]:
        """批量迁移配置文件
        
        Args:
            source_dir: 源配置目录
            target_dir: 目标配置目录
            config_type: 配置类型
            backup: 是否创建备份
            
        Returns:
            迁移结果列表
        """
        source_dir = Path(source_dir)
        target_dir = Path(target_dir)
        
        results = []
        
        # 查找所有YAML配置文件
        yaml_files = list(source_dir.rglob("*.yaml")) + list(source_dir.rglob("*.yml"))
        
        for yaml_file in yaml_files:
            # 计算相对路径
            relative_path = yaml_file.relative_to(source_dir)
            target_file = target_dir / relative_path
            
            # 迁移单个文件
            result = self.migrate_config(yaml_file, target_file, config_type, backup)
            results.append(result)
        
        return results
    
    def generate_migration_report(self, results: List[MigrationResult]) -> Dict[str, Any]:
        """生成迁移报告
        
        Args:
            results: 迁移结果列表
            
        Returns:
            迁移报告
        """
        total_count = len(results)
        success_count = sum(1 for r in results if r.success)
        failed_count = total_count - success_count
        
        all_errors = []
        all_warnings = []
        
        for result in results:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_files": total_count,
            "successful_files": success_count,
            "failed_files": failed_count,
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "errors": all_errors,
            "warnings": all_warnings,
            "detailed_results": [
                {
                    "source_path": r.source_path,
                    "target_path": r.target_path,
                    "success": r.success,
                    "errors": r.errors,
                    "warnings": r.warnings
                }
                for r in results
            ]
        }


# 便捷的迁移函数
def migrate_workflow_config(
    source_path: Union[str, Path], 
    target_path: Union[str, Path], 
    backup: bool = True
) -> MigrationResult:
    """迁移工作流配置
    
    Args:
        source_path: 源配置文件路径
        target_path: 目标配置文件路径
        backup: 是否创建备份
        
    Returns:
        迁移结果
    """
    tool = ConfigMigrationTool()
    return tool.migrate_config(source_path, target_path, ConfigType.WORKFLOW, backup)


def migrate_agent_config(
    source_path: Union[str, Path], 
    target_path: Union[str, Path], 
    backup: bool = True
) -> MigrationResult:
    """迁移Agent配置
    
    Args:
        source_path: 源配置文件路径
        target_path: 目标配置文件路径
        backup: 是否创建备份
        
    Returns:
        迁移结果
    """
    tool = ConfigMigrationTool()
    return tool.migrate_config(source_path, target_path, ConfigType.AGENT, backup)


def migrate_tool_config(
    source_path: Union[str, Path], 
    target_path: Union[str, Path], 
    backup: bool = True
) -> MigrationResult:
    """迁移工具配置
    
    Args:
        source_path: 源配置文件路径
        target_path: 目标配置文件路径
        backup: 是否创建备份
        
    Returns:
        迁移结果
    """
    tool = ConfigMigrationTool()
    return tool.migrate_config(source_path, target_path, ConfigType.TOOL, backup)


def migrate_llm_config(
    source_path: Union[str, Path], 
    target_path: Union[str, Path], 
    backup: bool = True
) -> MigrationResult:
    """迁移LLM配置
    
    Args:
        source_path: 源配置文件路径
        target_path: 目标配置文件路径
        backup: 是否创建备份
        
    Returns:
        迁移结果
    """
    tool = ConfigMigrationTool()
    return tool.migrate_config(source_path, target_path, ConfigType.LLM, backup)


def migrate_graph_config(
    source_path: Union[str, Path], 
    target_path: Union[str, Path], 
    backup: bool = True
) -> MigrationResult:
    """迁移图配置
    
    Args:
        source_path: 源配置文件路径
        target_path: 目标配置文件路径
        backup: 是否创建备份
        
    Returns:
        迁移结果
    """
    tool = ConfigMigrationTool()
    return tool.migrate_config(source_path, target_path, ConfigType.GRAPH, backup)