"""注册表配置验证器

专门验证注册表配置的结构和内容。
"""

from typing import Dict, List, Any, Optional
import os
from src.core.config.validation.validation import BaseConfigValidator, ValidationResult, ValidationSeverity


class RegistryConfigValidator(BaseConfigValidator):
    """注册表配置验证器
    
    继承基础验证器，专门验证注册表配置。
    """
    
    def __init__(self, registry_type: str = "registry"):
        """初始化注册表验证器
        
        Args:
            registry_type: 注册表类型（workflows, tools等）
        """
        super().__init__(f"{registry_type}RegistryValidator")
        self.registry_type = registry_type
    
    def _validate_custom(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """自定义验证逻辑
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        # 验证元数据
        self._validate_metadata(config, result)
        
        # 根据注册表类型验证特定内容
        if self.registry_type == "workflows":
            self._validate_workflow_registry(config, result)
        elif self.registry_type == "tools":
            self._validate_tool_registry(config, result)
        elif self.registry_type == "state_machine":
            self._validate_state_machine_registry(config, result)
        
        # 验证验证规则
        self._validate_validation_rules(config, result)
        
        # 验证自动发现配置
        self._validate_auto_discovery(config, result)
    
    def _validate_metadata(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """验证元数据
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        if "metadata" not in config:
            result.add_warning("缺少元数据部分")
            return
        
        metadata = config["metadata"]
        if not isinstance(metadata, dict):
            result.add_error("元数据必须是字典类型")
            return
        
        # 验证必需的元数据字段
        required_fields = ["name", "version", "description"]
        self._validate_required_fields(metadata, required_fields, result)
        
        # 验证字段类型
        type_rules = {
            "name": str,
            "version": str,
            "description": str,
            "author": str
        }
        self._validate_field_types(metadata, type_rules, result)
        
        # 验证版本格式
        if "version" in metadata:
            version = metadata["version"]
            if isinstance(version, str):
                # 简单的语义版本验证
                if not version.count(".") >= 2:
                    result.add_warning(f"版本格式可能不标准: {version}，建议使用语义版本格式 (如 1.0.0)")
    
    def _validate_workflow_registry(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """验证工作流注册表
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        if "workflow_types" not in config:
            result.add_error("工作流注册表必须包含 workflow_types 部分")
            return
        
        workflow_types = config["workflow_types"]
        if not isinstance(workflow_types, dict):
            result.add_error("workflow_types 必须是字典类型")
            return
        
        # 验证每个工作流类型
        for workflow_name, workflow_config in workflow_types.items():
            self._validate_workflow_type(workflow_name, workflow_config, result)
        
        # 验证状态机工作流配置
        if "state_machine_workflows" in config:
            self._validate_state_machine_workflows_config(config["state_machine_workflows"], result)
    
    def _validate_workflow_type(self, name: str, config: Any, result: ValidationResult) -> None:
        """验证单个工作流类型
        
        Args:
            name: 工作流类型名称
            config: 工作流类型配置
            result: 验证结果
        """
        if not isinstance(config, dict):
            result.add_error(f"工作流类型 '{name}' 的配置必须是字典类型")
            return
        
        # 验证必需字段
        required_fields = ["class_path", "description", "enabled", "config_files"]
        self._validate_required_fields(config, required_fields, result)
        
        # 验证字段类型
        type_rules = {
            "class_path": str,
            "description": str,
            "enabled": bool,
            "config_files": list
        }
        self._validate_field_types(config, type_rules, result)
        
        # 验证类路径
        if "class_path" in config:
            self._validate_class_path(config["class_path"], result)
        
        # 验证配置文件列表
        if "config_files" in config:
            config_files = config["config_files"]
            if not config_files:
                result.add_warning(f"工作流类型 '{name}' 的配置文件列表为空")
            
            for config_file in config_files:
                if not isinstance(config_file, str):
                    result.add_error(f"工作流类型 '{name}' 的配置文件名必须是字符串: {config_file}")
                else:
                    self._validate_file_path(config_file, result)
    
    def _validate_state_machine_workflows_config(self, config: Any, result: ValidationResult) -> None:
        """验证状态机工作流配置
        
        Args:
            config: 状态机工作流配置
            result: 验证结果
        """
        if not isinstance(config, dict):
            result.add_error("state_machine_workflows 必须是字典类型")
            return
        
        # 验证注册表文件路径
        if "registry_file" in config:
            registry_file = config["registry_file"]
            if not isinstance(registry_file, str):
                result.add_error("registry_file 必须是字符串类型")
            else:
                self._validate_file_path(registry_file, result)
    
    def _validate_tool_registry(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """验证工具注册表
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        if "tool_types" not in config:
            result.add_error("工具注册表必须包含 tool_types 部分")
            return
        
        tool_types = config["tool_types"]
        if not isinstance(tool_types, dict):
            result.add_error("tool_types 必须是字典类型")
            return
        
        # 验证每个工具类型
        for tool_name, tool_config in tool_types.items():
            self._validate_tool_type(tool_name, tool_config, result)
        
        # 验证工具集配置
        if "tool_sets" in config:
            self._validate_tool_sets(config["tool_sets"], result)
    
    def _validate_tool_type(self, name: str, config: Any, result: ValidationResult) -> None:
        """验证单个工具类型
        
        Args:
            name: 工具类型名称
            config: 工具类型配置
            result: 验证结果
        """
        if not isinstance(config, dict):
            result.add_error(f"工具类型 '{name}' 的配置必须是字典类型")
            return
        
        # 验证必需字段
        required_fields = ["class_path", "description", "enabled"]
        self._validate_required_fields(config, required_fields, result)
        
        # 验证字段类型
        type_rules = {
            "class_path": str,
            "description": str,
            "enabled": bool,
            "config_files": list
        }
        self._validate_field_types(config, type_rules, result)
        
        # 验证类路径
        if "class_path" in config:
            self._validate_class_path(config["class_path"], result)
        
        # 验证配置文件列表（可选）
        if "config_files" in config:
            config_files = config["config_files"]
            if not isinstance(config_files, list):
                result.add_error(f"工具类型 '{name}' 的 config_files 必须是列表类型")
            else:
                for config_file in config_files:
                    if not isinstance(config_file, str):
                        result.add_error(f"工具类型 '{name}' 的配置文件名必须是字符串: {config_file}")
    
    def _validate_tool_sets(self, tool_sets: Any, result: ValidationResult) -> None:
        """验证工具集配置
        
        Args:
            tool_sets: 工具集配置
            result: 验证结果
        """
        if not isinstance(tool_sets, dict):
            result.add_error("tool_sets 必须是字典类型")
            return
        
        # 验证每个工具集
        for set_name, set_config in tool_sets.items():
            if not isinstance(set_config, dict):
                result.add_error(f"工具集 '{set_name}' 的配置必须是字典类型")
                continue
            
            # 验证必需字段
            required_fields = ["description", "enabled", "tools"]
            self._validate_required_fields(set_config, required_fields, result)
            
            # 验证字段类型
            type_rules = {
                "description": str,
                "enabled": bool,
                "tools": list
            }
            self._validate_field_types(set_config, type_rules, result)
            
            # 验证工具列表
            if "tools" in set_config:
                tools = set_config["tools"]
                if not isinstance(tools, list):
                    result.add_error(f"工具集 '{set_name}' 的 tools 必须是列表类型")
                elif not tools:
                    result.add_warning(f"工具集 '{set_name}' 的工具列表为空")
    
    def _validate_state_machine_registry(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """验证状态机注册表
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        if "config_files" not in config:
            result.add_error("状态机注册表必须包含 config_files 部分")
            return
        
        config_files = config["config_files"]
        if not isinstance(config_files, dict):
            result.add_error("config_files 必须是字典类型")
            return
        
        # 验证每个配置文件
        for config_name, config_info in config_files.items():
            if not isinstance(config_info, dict):
                result.add_error(f"配置文件 '{config_name}' 的信息必须是字典类型")
                continue
            
            # 验证必需字段
            required_fields = ["file_path", "description", "enabled"]
            self._validate_required_fields(config_info, required_fields, result)
            
            # 验证字段类型
            type_rules = {
                "file_path": str,
                "description": str,
                "enabled": bool
            }
            self._validate_field_types(config_info, type_rules, result)
            
            # 验证文件路径
            if "file_path" in config_info:
                self._validate_file_path(config_info["file_path"], result)
    
    def _validate_validation_rules(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """验证验证规则
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        if "validation_rules" not in config:
            return
        
        validation_rules = config["validation_rules"]
        if not isinstance(validation_rules, list):
            result.add_error("validation_rules 必须是列表类型")
            return
        
        # 验证每个规则
        for i, rule in enumerate(validation_rules):
            if not isinstance(rule, dict):
                result.add_error(f"验证规则 {i} 必须是字典类型")
                continue
            
            # 验证必需字段
            required_fields = ["field", "rule_type", "message"]
            self._validate_required_fields(rule, required_fields, result)
            
            # 验证字段类型
            type_rules = {
                "field": str,
                "rule_type": str,
                "message": str
            }
            self._validate_field_types(rule, type_rules, result)
            
            # 验证规则类型
            if "rule_type" in rule:
                valid_rule_types = ["required", "boolean", "list", "range", "pattern", "enum"]
                if rule["rule_type"] not in valid_rule_types:
                    result.add_warning(f"未知的规则类型: {rule['rule_type']}，支持的类型: {valid_rule_types}")
    
    def _validate_auto_discovery(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """验证自动发现配置
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        if "auto_discovery" not in config:
            return
        
        auto_discovery = config["auto_discovery"]
        if not isinstance(auto_discovery, dict):
            result.add_error("auto_discovery 必须是字典类型")
            return
        
        # 验证字段类型
        type_rules = {
            "enabled": bool,
            "scan_directories": list,
            "file_patterns": list,
            "exclude_patterns": list
        }
        self._validate_field_types(auto_discovery, type_rules, result)
        
        # 验证扫描目录
        if "scan_directories" in auto_discovery:
            scan_dirs = auto_discovery["scan_directories"]
            for scan_dir in scan_dirs:
                if not isinstance(scan_dir, str):
                    result.add_error(f"扫描目录必须是字符串: {scan_dir}")
        
        # 验证文件模式
        if "file_patterns" in auto_discovery:
            file_patterns = auto_discovery["file_patterns"]
            for pattern in file_patterns:
                if not isinstance(pattern, str):
                    result.add_error(f"文件模式必须是字符串: {pattern}")
        
        # 验证排除模式
        if "exclude_patterns" in auto_discovery:
            exclude_patterns = auto_discovery["exclude_patterns"]
            for pattern in exclude_patterns:
                if not isinstance(pattern, str):
                    result.add_error(f"排除模式必须是字符串: {pattern}")