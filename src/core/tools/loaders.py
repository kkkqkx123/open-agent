"""
工具加载器实现

提供工具配置的加载和解析功能。
"""

import os
from typing import List, Dict, Any
from pathlib import Path

from .interfaces import ITool
from .config import ToolConfig

class DefaultToolLoader:
    """默认工具加载器实现"""
    
    def __init__(self, config_loader, logger):
        """初始化工具加载器
        
        Args:
            config_loader: 配置加载器
            logger: 日志记录器
        """
        self.config_loader = config_loader
        self.logger = logger
    
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
            tool_type: 工具类型 (rest, rest, mcp)
            
        Returns:
            List[ToolConfig]: 工具配置列表
        """
        tool_configs = []
        
        # 构建配置目录路径
        config_dir_path = os.path.join("configs", "tools", tool_type)
        self.logger.info(f"配置目录路径: {config_dir_path}")
        
        # 检查目录是否存在
        if not os.path.exists(config_dir_path):
            self.logger.warning(f"配置目录不存在: {config_dir_path}")
            return tool_configs
        
        # 遍历目录中的所有YAML文件
        yaml_files = [f for f in os.listdir(config_dir_path) if f.endswith('.yaml')]
        self.logger.info(f"找到 {len(yaml_files)} 个YAML配置文件")
        
        for yaml_file in yaml_files:
            try:
                full_path = os.path.join("tools", tool_type, yaml_file)
                self.logger.info(f"Loading tool config from {full_path}")
                # 加载配置文件
                config_data = self.config_loader.load(full_path)
                self.logger.info(f"成功加载配置文件 {full_path}")
                
                # 解析工具配置
                tool_config = self._parse_tool_config(config_data)
                tool_configs.append(tool_config)
                self.logger.info(f"Successfully loaded tool config: {tool_config.name}")
                
            except Exception as e:
                self.logger.error(f"加载工具配置文件失败 {yaml_file}: {str(e)}")
                # 继续加载其他配置文件
                continue
        
        return tool_configs
    
    def _parse_tool_config(self, config_data: Dict[str, Any]) -> ToolConfig:
        """解析工具配置
        
        Args:
            config_data: 配置数据
            
        Returns:
            ToolConfig: 工具配置对象
            
        Raises:
            ValueError: 配置格式错误
        """
        from .config import (
            RestToolConfig,
            MCPToolConfig,
            RestToolConfig
        )
        
        tool_type = config_data.get("tool_type")
        if not tool_type:
            raise ValueError("缺少tool_type配置")
        
        if tool_type == "rest":
            return RestToolConfig(**config_data)
        elif tool_type == "rest":
            return RestToolConfig(**config_data)
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
    
    def __init__(self, config_loader, logger, registry_config: Dict[str, Any]):
        """初始化基于注册表的工具加载器
        
        Args:
            config_loader: 配置加载器
            logger: 日志记录器
            registry_config: 注册表配置
        """
        self.config_loader = config_loader
        self.logger = logger
        self.registry_config = registry_config
    
    def load_all_tools(self) -> List[ToolConfig]:
        """从注册表加载所有工具
        
        Returns:
            List[ToolConfig]: 加载的工具配置列表
        """
        tool_configs = []
        
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
                        config_data = self.config_loader.load(config_path)
                        
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
            ToolConfig: 工具配置对象
        """
        from .config import (
            RestToolConfig,
            MCPToolConfig,
            RestToolConfig
        )
        
        tool_type = config_data.get("tool_type")
        if not tool_type:
            raise ValueError("缺少tool_type配置")
        
        if tool_type == "rest":
            return RestToolConfig(**config_data)
        elif tool_type == "rest":
            return RestToolConfig(**config_data)
        elif tool_type == "mcp":
            return MCPToolConfig(**config_data)
        else:
            raise ValueError(f"未知的工具类型: {tool_type}")