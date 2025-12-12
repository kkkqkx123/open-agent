"""
工具加载器实现

提供工具配置的加载和解析功能。
"""

import os
import logging
from src.interfaces.dependency_injection import get_logger
from typing import List, Dict, Any, Union, Optional
from src.interfaces.tool.base import ITool
from src.interfaces.tool.config import ToolConfig, RestToolConfig, MCPToolConfig, NativeToolConfig
from ..config.config_manager import ConfigManager
from src.interfaces.dependency_injection.config import get_config_manager

logger = get_logger(__name__)

class DefaultToolLoader:
    """默认工具加载器实现"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, logger_arg: Optional[logging.Logger] = None):
        """初始化工具加载器
         
        Args:
            config_manager: 配置管理器，如果为None则使用默认管理器
            logger_arg: 日志记录器
        """
        self.config_manager = config_manager or get_config_manager()
        self.logger = logger_arg or logger
    
    def load_from_config(self, config_path: str) -> List[ToolConfig]:
        """从配置文件加载工具配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            List[ToolConfig]: 加载的工具配置列表
        """
        self.logger.info(f"开始加载工具配置，配置路径: {config_path}")
        tool_configs = []
        
        try:
            # 支持新的分类目录结构
            if config_path == "tools":
                # 加载所有分类的工具
                tool_types = ["rest", "rest", "mcp"]
                for tool_type in tool_types:
                    type_configs = self._load_tool_type_configs(tool_type)
                    tool_configs.extend(type_configs)
            else:
                # 加载指定路径的工具配置
                type_configs = self._load_tool_type_configs(config_path)
                tool_configs.extend(type_configs)
            
            self.logger.info(f"总共加载了 {len(tool_configs)} 个工具配置")
            return tool_configs
            
        except Exception as e:
            self.logger.error(f"加载工具配置失败: {str(e)}")
            # from src.infrastructure.exceptions import InfrastructureError
            # raise InfrastructureError(f"加载工具配置失败: {str(e)}")
            raise Exception(f"加载工具配置失败: {str(e)}")
    
    def _load_tool_type_configs(self, tool_type: str) -> List[ToolConfig]:
        """加载指定工具类型的配置
         
        Args:
            tool_type: 工具类型 (rest, native, mcp)
             
        Returns:
            List[ToolConfig]: 工具配置列表
        """
        tool_configs: List[ToolConfig] = []
         
        # 构建配置目录路径
        config_dir_path = os.path.join("configs", "tools", tool_type)
        self.logger.info(f"配置目录路径: {config_dir_path}")
         
        # 检查目录是否存在
        if not os.path.exists(config_dir_path):
            self.logger.warning(f"配置目录不存在: {config_dir_path}")
            return tool_configs
         
        # 使用配置管理器列出配置文件
        try:
            config_files = self.config_manager.list_config_files(f"tools/{tool_type}")
            self.logger.info(f"找到 {len(config_files)} 个工具配置文件")
             
            for config_file in config_files:
                try:
                    full_path = f"tools/{tool_type}/{config_file}"
                    self.logger.info(f"Loading tool config from {full_path}")
                    # 使用统一配置管理器加载
                    config_data = self.config_manager.load_config(full_path, "tools")
                    self.logger.info(f"成功加载配置文件 {full_path}")
                     
                    # 解析工具配置
                    tool_config = self._parse_tool_config(config_data)
                    tool_configs.append(tool_config)
                    self.logger.info(f"Successfully loaded tool config: {tool_config.name}")
                     
                except Exception as e:
                    self.logger.error(f"加载工具配置文件失败 {config_file}: {str(e)}")
                    # 继续加载其他配置文件
                    continue
             
        except Exception as e:
            self.logger.error(f"列出工具配置文件失败: {str(e)}")
         
        return tool_configs
    
    def _parse_tool_config(self, config_data: Dict[str, Any]) -> ToolConfig:
        """解析工具配置
        
        Args:
            config_data: 配置数据
            
        Returns:
            Union[RestToolConfig, MCPToolConfig, NativeToolConfig]: 工具配置对象
            
        Raises:
            ValueError: 配置格式错误
        """
        
        tool_type = config_data.get("tool_type")
        if not tool_type:
            raise ValueError("缺少tool_type配置")
        
        if tool_type == "rest":
            return RestToolConfig(**config_data)
        elif tool_type == "native":
            return NativeToolConfig(**config_data)
        elif tool_type == "mcp":
            return MCPToolConfig(**config_data)
        else:
            raise ValueError(f"未知的工具类型: {tool_type}")
    
    def load_from_module(self, module_path: str) -> List["ITool"]:
        """从模块加载工具
        
        Args:
            module_path: 模块路径
            
        Returns:
            List[ITool]: 加载的工具列表
        """
        # 这个方法在当前实现中暂不支持
        raise NotImplementedError("从模块加载工具功能暂未实现")


class RegistryBasedToolLoader:
    """基于注册表的工具加载器"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, logger_arg: Optional[logging.Logger] = None, registry_config: Optional[Dict[str, Any]] = None):
        """初始化基于注册表的工具加载器
         
        Args:
            config_manager: 配置管理器，如果为None则使用默认管理器
            logger_arg: 日志记录器
            registry_config: 注册表配置
        """
        self.config_manager = config_manager or get_config_manager()
        self.logger = logger_arg or logger
        self.registry_config = registry_config or {}
    
    def load_all_tools(self) -> List[ToolConfig]:
        """从注册表加载所有工具
        
        Returns:
            List[ToolConfig]: 加载的工具配置列表
        """
        tool_configs: List[ToolConfig] = []
        
        try:
            tool_types = self.registry_config.get("tool_types", {})
            
            for tool_type, type_config in tool_types.items():
                if not type_config.get("enabled", True):
                    self.logger.info(f"跳过禁用的工具类型: {tool_type}")
                    continue
                
                # 获取配置目录
                config_directory = type_config.get("config_directory", tool_type)
                config_files = type_config.get("config_files", [])
                
                # 加载该类型的所有配置文件
                for config_file in config_files:
                    try:
                        config_path = os.path.join("tools", config_directory, config_file)
                        config_data = self.config_manager.load_config(config_path, "tools")
                        
                        # 确保工具类型正确
                        config_data["tool_type"] = tool_type
                        
                        # 解析工具配置
                        tool_config = self._parse_tool_config(config_data)
                        tool_configs.append(tool_config)
                        
                        self.logger.info(f"成功加载工具配置: {tool_config.name}")
                        
                    except Exception as e:
                        self.logger.error(f"加载工具配置失败 {config_file}: {str(e)}")
                        continue
            
            self.logger.info(f"总共加载了 {len(tool_configs)} 个工具配置")
            return tool_configs
            
        except Exception as e:
            self.logger.error(f"从注册表加载工具失败: {str(e)}")
            raise Exception(f"从注册表加载工具失败: {str(e)}")
    
    def _parse_tool_config(self, config_data: Dict[str, Any]) -> ToolConfig:
        """解析工具配置
        
        Args:
            config_data: 配置数据
            
        Returns:
            Union[RestToolConfig, MCPToolConfig, NativeToolConfig]: 工具配置对象
        """
        
        tool_type = config_data.get("tool_type")
        if not tool_type:
            raise ValueError("缺少tool_type配置")
        
        if tool_type == "rest":
            return RestToolConfig(**config_data)
        elif tool_type == "native":
            return NativeToolConfig(**config_data)
        elif tool_type == "mcp":
            return MCPToolConfig(**config_data)
        else:
            raise ValueError(f"未知的工具类型: {tool_type}")