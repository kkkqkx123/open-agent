"""模块注册管理器

管理各模块的注册表配置加载，提供类型和配置文件的获取接口。
"""

from typing import Dict, List, Any, Optional, Type, Union
from pathlib import Path
import logging
from dataclasses import dataclass, field

from .config_parser import ConfigParser, ConfigParseError
from .dynamic_importer import DynamicImporter
from .config_validator import ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class RegistryInfo:
    """注册表信息"""
    name: str
    config_path: str
    config: Dict[str, Any] = field(default_factory=dict)
    validation_result: Optional[ValidationResult] = None
    loaded: bool = False
    enabled: bool = True


@dataclass
class TypeInfo:
    """类型信息"""
    name: str
    class_path: str
    description: str
    enabled: bool
    config_files: List[str] = field(default_factory=list)
    class_instance: Optional[Type] = None
    loaded: bool = False


class ModuleRegistryManager:
    """模块注册管理器
    
    管理各模块的注册表配置加载，提供类型和配置文件的获取接口。
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """初始化模块注册管理器
        
        Args:
            base_path: 配置文件基础路径
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.logger = logging.getLogger(f"{__name__}.ModuleRegistryManager")
        
        # 初始化组件
        self.config_parser = ConfigParser(str(self.base_path))
        self.dynamic_importer = DynamicImporter()
        
        # 注册表信息
        self.registries: Dict[str, RegistryInfo] = {}
        
        # 类型信息
        self.workflow_types: Dict[str, TypeInfo] = {}
        self.tool_types: Dict[str, TypeInfo] = {}
        self.state_machine_configs: Dict[str, Dict[str, Any]] = {}
        
        # 工具集信息
        self.tool_sets: Dict[str, Dict[str, Any]] = {}
        
        # 配置缓存
        self.config_cache: Dict[str, Dict[str, Any]] = {}
        
        # 初始化状态
        self.initialized = False
    
    def initialize(self) -> None:
        """初始化注册管理器
         
        加载所有注册表配置并注册类型。
        """
        if self.initialized:
            self.logger.debug("注册管理器已初始化")
            return
         
        try:
            self.logger.info("开始初始化模块注册管理器")
             
            # 加载工作流注册表
            self._load_workflow_registry()
             
            # 加载工具注册表
            self._load_tool_registry()
             
            # 加载状态机工作流注册表
            self._load_state_machine_registry()
             
            self.initialized = True
            self.logger.info("模块注册管理器初始化完成")
             
        except Exception as e:
            self.logger.error(f"初始化模块注册管理器失败: {e}")
            # 不抛出异常，保持initialized为False
            self.initialized = False
    
    def get_workflow_type(self, workflow_type: str) -> Optional[TypeInfo]:
        """获取工作流类型信息
        
        Args:
            workflow_type: 工作流类型名称
            
        Returns:
            Optional[TypeInfo]: 类型信息，如果不存在则返回None
        """
        if not self.initialized:
            self.logger.warning("注册管理器未初始化")
            return None
        
        return self.workflow_types.get(workflow_type)
    
    def get_tool_type(self, tool_type: str) -> Optional[TypeInfo]:
        """获取工具类型信息
        
        Args:
            tool_type: 工具类型名称
            
        Returns:
            Optional[TypeInfo]: 类型信息，如果不存在则返回None
        """
        if not self.initialized:
            self.logger.warning("注册管理器未初始化")
            return None
        
        return self.tool_types.get(tool_type)
    
    def get_workflow_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """获取工作流配置
        
        Args:
            config_name: 配置名称
            
        Returns:
            Optional[Dict[str, Any]]: 配置数据，如果不存在则返回None
        """
        if not self.initialized:
            self.logger.warning("注册管理器未初始化")
            return None
        
        # 检查缓存
        if config_name in self.config_cache:
            return self.config_cache[config_name]
        
        # 查找配置文件
        for registry_info in self.registries.values():
            if not registry_info.loaded or not registry_info.enabled:
                continue
            
            config = registry_info.config
            
            # 工作流注册表
            if "workflow_types" in config:
                workflow_types = config["workflow_types"]
                for type_name, type_config in workflow_types.items():
                    if type_name == config_name:
                        # 加载配置文件
                        config_files = type_config.get("config_files", [])
                        if config_files:
                            config_file = config_files[0]  # 使用第一个配置文件
                            try:
                                full_config = self.config_parser.parse_workflow_config(
                                    f"workflows/{config_file}"
                                )
                                self.config_cache[config_name] = full_config
                                return full_config
                            except Exception as e:
                                self.logger.error(f"加载工作流配置失败: {config_file}, 错误: {e}")
                                return None
            
            # 状态机工作流注册表
            if "config_files" in config:
                config_files = config["config_files"]
                if config_name in config_files:
                    config_info = config_files[config_name]
                    if config_info.get("enabled", True):
                        file_path = config_info["file_path"]
                        try:
                            full_config = self.config_parser.parse_workflow_config(
                                f"workflows/{file_path}"
                            )
                            self.config_cache[config_name] = full_config
                            return full_config
                        except Exception as e:
                            self.logger.error(f"加载状态机工作流配置失败: {file_path}, 错误: {e}")
                            return None
        
        return None
    
    def get_tool_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """获取工具配置
        
        Args:
            config_name: 配置名称
            
        Returns:
            Optional[Dict[str, Any]]: 配置数据，如果不存在则返回None
        """
        if not self.initialized:
            self.logger.warning("注册管理器未初始化")
            return None
        
        # 检查缓存
        if config_name in self.config_cache:
            return self.config_cache[config_name]
        
        # 查找配置文件
        registry_info = self.registries.get("tools")
        if not registry_info or not registry_info.loaded or not registry_info.enabled:
            return None
        
        config = registry_info.config
        
        # 工具注册表
        if "tool_types" in config:
            tool_types = config["tool_types"]
            for type_name, type_config in tool_types.items():
                if type_name == config_name:
                    # 加载配置文件
                    config_files = type_config.get("config_files", [])
                    if config_files:
                        config_file = config_files[0]  # 使用第一个配置文件
                        try:
                            full_config = self.config_parser.parse_tool_config(
                                f"tools/{config_file}"
                            )
                            self.config_cache[config_name] = full_config
                            return full_config
                        except Exception as e:
                            self.logger.error(f"加载工具配置失败: {config_file}, 错误: {e}")
                            return None
        
        return None
    
    def get_tool_set(self, set_name: str) -> Optional[Dict[str, Any]]:
        """获取工具集
        
        Args:
            set_name: 工具集名称
            
        Returns:
            Optional[Dict[str, Any]]: 工具集配置，如果不存在则返回None
        """
        if not self.initialized:
            self.logger.warning("注册管理器未初始化")
            return None
        
        return self.tool_sets.get(set_name)
    
    def get_workflow_types(self) -> Dict[str, TypeInfo]:
        """获取所有工作流类型
        
        Returns:
            Dict[str, TypeInfo]: 工作流类型字典
        """
        if not self.initialized:
            self.logger.warning("注册管理器未初始化")
            return {}
        
        return self.workflow_types.copy()
    
    def get_tool_types(self) -> Dict[str, TypeInfo]:
        """获取所有工具类型
        
        Returns:
            Dict[str, TypeInfo]: 工具类型字典
        """
        if not self.initialized:
            self.logger.warning("注册管理器未初始化")
            return {}
        
        return self.tool_types.copy()
    
    def get_state_machine_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有状态机配置
        
        Returns:
            Dict[str, Dict[str, Any]]: 状态机配置字典
        """
        if not self.initialized:
            self.logger.warning("注册管理器未初始化")
            return {}
        
        return self.state_machine_configs.copy()
    
    def reload_registry(self, registry_type: str) -> None:
        """重新加载注册表
        
        Args:
            registry_type: 注册表类型（workflows, tools, state_machine）
        """
        if not self.initialized:
            self.logger.warning("注册管理器未初始化")
            return
        
        self.logger.info(f"重新加载注册表: {registry_type}")
        
        try:
            if registry_type == "workflows":
                self._load_workflow_registry()
            elif registry_type == "tools":
                self._load_tool_registry()
            elif registry_type == "state_machine":
                self._load_state_machine_registry()
            else:
                self.logger.error(f"不支持的注册表类型: {registry_type}")
                
        except Exception as e:
            self.logger.error(f"重新加载注册表失败: {registry_type}, 错误: {e}")
    
    def clear_cache(self) -> None:
        """清除缓存"""
        self.config_cache.clear()
        self.config_parser.clear_cache()
        self.logger.info("已清除缓存")
    
    def get_registry_info(self) -> Dict[str, Any]:
        """获取注册表信息
        
        Returns:
            Dict[str, Any]: 注册表信息
        """
        return {
            "initialized": self.initialized,
            "registries": {
                name: {
                    "config_path": info.config_path,
                    "loaded": info.loaded,
                    "enabled": info.enabled,
                    "validation_errors": len(info.validation_result.errors) if info.validation_result else 0,
                    "validation_warnings": len(info.validation_result.warnings) if info.validation_result else 0
                }
                for name, info in self.registries.items()
            },
            "workflow_types": len(self.workflow_types),
            "tool_types": len(self.tool_types),
            "state_machine_configs": len(self.state_machine_configs),
            "tool_sets": len(self.tool_sets),
            "cache_size": len(self.config_cache)
        }
    
    def _load_workflow_registry(self) -> None:
        """加载工作流注册表"""
        try:
            config_path = "workflows/__registry__.yaml"
            config = self.config_parser.parse_registry_config("workflows", config_path)
            
            # 创建注册表信息
            registry_info = RegistryInfo(
                name="workflows",
                config_path=config_path,
                config=config,
                validation_result=self.config_parser.get_validation_result("workflows", config_path),
                loaded=True,
                enabled=True
            )
            self.registries["workflows"] = registry_info
            
            # 解析工作流类型
            if "workflow_types" in config:
                for type_name, type_config in config["workflow_types"].items():
                    type_info = TypeInfo(
                        name=type_name,
                        class_path=type_config["class_path"],
                        description=type_config["description"],
                        enabled=type_config.get("enabled", True),
                        config_files=type_config.get("config_files", [])
                    )
                    self.workflow_types[type_name] = type_info
            
            self.logger.info(f"成功加载工作流注册表，注册了 {len(self.workflow_types)} 个工作流类型")
            
        except Exception as e:
            self.logger.error(f"加载工作流注册表失败: {e}")
            raise
    
    def _load_tool_registry(self) -> None:
        """加载工具注册表"""
        try:
            config_path = "tools/__registry__.yaml"
            config = self.config_parser.parse_registry_config("tools", config_path)
            
            # 创建注册表信息
            registry_info = RegistryInfo(
                name="tools",
                config_path=config_path,
                config=config,
                validation_result=self.config_parser.get_validation_result("tools", config_path),
                loaded=True,
                enabled=True
            )
            self.registries["tools"] = registry_info
            
            # 解析工具类型
            if "tool_types" in config:
                for type_name, type_config in config["tool_types"].items():
                    type_info = TypeInfo(
                        name=type_name,
                        class_path=type_config["class_path"],
                        description=type_config["description"],
                        enabled=type_config.get("enabled", True),
                        config_files=type_config.get("config_files", [])
                    )
                    self.tool_types[type_name] = type_info
            
            # 解析工具集
            if "tool_sets" in config:
                self.tool_sets = config["tool_sets"]
            
            self.logger.info(f"成功加载工具注册表，注册了 {len(self.tool_types)} 个工具类型")
            
        except Exception as e:
            self.logger.error(f"加载工具注册表失败: {e}")
            raise
    
    def _load_state_machine_registry(self) -> None:
        """加载状态机工作流注册表"""
        try:
            config_path = "workflows/state_machine/__registry__.yaml"
            config = self.config_parser.parse_registry_config("state_machine", config_path)
            
            # 创建注册表信息
            registry_info = RegistryInfo(
                name="state_machine",
                config_path=config_path,
                config=config,
                validation_result=self.config_parser.get_validation_result("state_machine", config_path),
                loaded=True,
                enabled=True
            )
            self.registries["state_machine"] = registry_info
            
            # 解析状态机配置
            if "config_files" in config:
                for config_name, config_info in config["config_files"].items():
                    if config_info.get("enabled", True):
                        file_path = config_info["file_path"]
                        try:
                            full_config = self.config_parser.parse_workflow_config(
                                f"workflows/{file_path}"
                            )
                            self.state_machine_configs[config_name] = full_config
                        except Exception as e:
                            self.logger.error(f"加载状态机工作流配置失败: {file_path}, 错误: {e}")
            
            self.logger.info(f"成功加载状态机工作流注册表，注册了 {len(self.state_machine_configs)} 个配置")
            
        except Exception as e:
            self.logger.error(f"加载状态机工作流注册表失败: {e}")
            raise