"""
工具加载器实现

提供工具配置的加载和解析功能。
"""

import os
from typing import List, Dict, Any
from pathlib import Path

from domain.tools.interfaces import ITool

from infrastructure.config.core.loader import IConfigLoader
from src.infrastructure.exceptions import InfrastructureError
from src.infrastructure.logger.logger import ILogger
from .interfaces import IToolLoader
from .config import ToolConfig


class DefaultToolLoader(IToolLoader):
    """默认工具加载器实现"""
    
    def __init__(self, config_loader: IConfigLoader, logger: ILogger):
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
            # 使用配置加载器加载配置目录
            # 注意：这里直接使用config_loader来获取目录下的所有配置文件
            import os
            config_dir_path = os.path.join("configs", config_path)
            self.logger.info(f"配置目录路径: {config_dir_path}")
            
            # 检查目录是否存在
            if not os.path.exists(config_dir_path):
                self.logger.warning(f"配置目录不存在: {config_dir_path}")
                return tool_configs
            
            # 遍历目录中的所有YAML文件
            yaml_files = [f for f in os.listdir(config_dir_path) if f.endswith('.yaml')]
            self.logger.info(f"找到 {len(yaml_files)} 个YAML配置文件")
            for f in yaml_files:
                self.logger.info(f"配置文件: {f}")
            
            for yaml_file in yaml_files:
                try:
                    full_path = os.path.join(config_path, yaml_file)
                    self.logger.info(f"Loading tool config from {full_path}")
                    # 加载配置文件
                    config_data = self.config_loader.load(full_path)
                    self.logger.info(f"成功加载配置文件 {full_path}: {config_data}")
                    
                    # 解析工具配置
                    tool_config = self._parse_tool_config(config_data)
                    tool_configs.append(tool_config)
                    self.logger.info(f"Successfully loaded tool config: {tool_config.name}")
                    
                except Exception as e:
                    self.logger.error(f"加载工具配置文件失败 {yaml_file}: {str(e)}")
                    # 继续加载其他配置文件
                    continue
            
            self.logger.info(f"总共加载了 {len(tool_configs)} 个工具配置")
            return tool_configs
            
        except Exception as e:
            self.logger.error(f"加载工具配置失败: {str(e)}")
            raise InfrastructureError(f"加载工具配置失败: {str(e)}")
    
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
            NativeToolConfig,
            MCPToolConfig,
            BuiltinToolConfig
        )
        
        tool_type = config_data.get("tool_type")
        if not tool_type:
            raise ValueError("缺少tool_type配置")
        
        if tool_type == "native":
            return NativeToolConfig(**config_data)
        elif tool_type == "mcp":
            return MCPToolConfig(**config_data)
        elif tool_type == "builtin":
            return BuiltinToolConfig(**config_data)
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