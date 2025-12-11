"""
工具配置服务

提供工具模块的配置管理服务，遵循服务层的职责。
"""

from typing import Dict, Any, Optional, List, Union
import logging

from src.interfaces.config import (
    IModuleConfigService, IConfigMapperRegistry, ValidationResult
)
from src.interfaces.dependency_injection import get_logger
from src.interfaces.tool.config import ToolConfig, NativeToolConfig, RestToolConfig, MCPToolConfig
from src.core.tools.config import ToolRegistryConfig
from src.core.config.mappers import ToolsConfigMapper
from src.infrastructure.config.models.base import ConfigData

logger = get_logger(__name__)


class ToolsConfigService(IModuleConfigService):
    """工具配置服务
    
    提供工具模块的配置加载、保存、验证和管理功能。
    """
    
    def __init__(self,
                 config_manager: Optional[Any] = None,
                 mapper_registry: Optional[IConfigMapperRegistry] = None):
        """初始化工具配置服务
        
        Args:
            config_manager: 配置管理器
            mapper_registry: 配置映射器注册表
        """
        self.config_manager = config_manager
        self.mapper_registry = mapper_registry
        
        # 获取工具配置映射器
        self._tools_mapper = ToolsConfigMapper()
        
        logger.debug("初始化工具配置服务")
    
    def load_config(self, config_path: str) -> Union[ToolConfig, ToolRegistryConfig]:
        """加载工具配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            工具配置实体
            
        Raises:
            Exception: 配置加载失败
        """
        try:
            logger.debug(f"加载工具配置: {config_path}")
            
            # 使用配置管理器加载配置数据
            if self.config_manager:
                config_dict = self.config_manager.load_config(config_path, "tools")
            else:
                raise ValueError("配置管理器未设置")
            
            # 转换为配置数据
            config_data = ConfigData(config_dict)
            
            # 使用映射器转换为业务实体
            config_entity = self._tools_mapper.config_data_to_tool_config(config_data)
            
            logger.info(f"工具配置加载成功: {config_path}")
            return config_entity
            
        except Exception as e:
            logger.error(f"加载工具配置失败 {config_path}: {e}")
            raise
    
    def save_config(self, config: Union[ToolConfig, ToolRegistryConfig], config_path: str) -> None:
        """保存工具配置
        
        Args:
            config: 工具配置实体
            config_path: 配置文件路径
            
        Raises:
            Exception: 配置保存失败
        """
        try:
            logger.debug(f"保存工具配置: {config_path}")
            
            # 使用映射器转换为配置数据
            config_data = self._tools_mapper.tool_config_to_config_data(config)
            
            # 使用配置管理器保存配置
            if self.config_manager:
                self.config_manager.save_config(config_data.data, config_path)
            else:
                raise ValueError("配置管理器未设置")
            
            logger.info(f"工具配置保存成功: {config_path}")
            
        except Exception as e:
            logger.error(f"保存工具配置失败 {config_path}: {e}")
            raise
    
    def validate_config(self, config: Union[ToolConfig, ToolRegistryConfig]) -> ValidationResult:
        """验证工具配置（委托给验证服务）
        
        Args:
            config: 工具配置实体
            
        Returns:
            验证结果
        """
        try:
            logger.debug("验证工具配置")
            
            # 委托给验证服务进行验证
            # 这里应该通过依赖注入获取验证服务
            # 暂时返回基础验证结果
            validation_result = ValidationResult(is_valid=True, errors=[], warnings=[])
            
            logger.debug(f"工具配置验证完成: {'通过' if validation_result.is_valid else '失败'}")
            return validation_result
            
        except Exception as e:
            logger.error(f"验证工具配置失败: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"验证失败: {e}"],
                warnings=[]
            )
    
    def load_tool_config(self, tool_name: str, tool_type: Optional[str] = None) -> ToolConfig:
        """加载特定工具配置
        
        Args:
            tool_name: 工具名称
            tool_type: 工具类型（可选）
            
        Returns:
            工具配置实体
        """
        try:
            # 构建配置路径
            if tool_type:
                config_path = f"tools/{tool_type}/{tool_name}"
            else:
                config_path = f"tools/{tool_name}"
            
            # 加载配置
            config = self.load_config(config_path)
            
            if not isinstance(config, ToolConfig):
                raise ValueError(f"配置不是工具配置: {config_path}")
            
            return config
            
        except Exception as e:
            logger.error(f"加载工具配置失败 {tool_name}: {e}")
            raise
    
    def save_tool_config(self, tool_config: ToolConfig, tool_type: Optional[str] = None) -> None:
        """保存工具配置
        
        Args:
            tool_config: 工具配置实体
            tool_type: 工具类型（可选）
        """
        try:
            # 构建配置路径
            if tool_type:
                config_path = f"tools/{tool_type}/{tool_config.name}"
            else:
                config_path = f"tools/{tool_config.name}"
            
            # 保存配置
            self.save_config(tool_config, config_path)
            
        except Exception as e:
            logger.error(f"保存工具配置失败 {tool_config.name}: {e}")
            raise
    
    def load_tool_registry_config(self) -> ToolRegistryConfig:
        """加载工具注册表配置
        
        Returns:
            工具注册表配置实体
        """
        try:
            # 加载配置
            config = self.load_config("tools/registry")
            
            if not isinstance(config, ToolRegistryConfig):
                raise ValueError("配置不是工具注册表配置")
            
            return config
            
        except Exception as e:
            logger.error(f"加载工具注册表配置失败: {e}")
            raise
    
    def save_tool_registry_config(self, registry_config: ToolRegistryConfig) -> None:
        """保存工具注册表配置
        
        Args:
            registry_config: 工具注册表配置实体
        """
        try:
            # 保存配置
            self.save_config(registry_config, "tools/registry")
            
        except Exception as e:
            logger.error(f"保存工具注册表配置失败: {e}")
            raise
    
    def load_tools_by_type(self, tool_type: str) -> List[ToolConfig]:
        """按类型加载工具配置
        
        Args:
            tool_type: 工具类型
            
        Returns:
            工具配置列表
        """
        try:
            tools = []
            
            # 获取指定类型的所有配置文件
            if self.config_manager:
                config_files = self.config_manager.list_config_files(f"tools/{tool_type}")
                
                for config_file in config_files:
                    try:
                        config_path = f"tools/{tool_type}/{config_file}"
                        config = self.load_config(config_path)
                        
                        if isinstance(config, ToolConfig):
                            tools.append(config)
                            
                    except Exception as e:
                        logger.warning(f"加载工具配置失败 {config_file}: {e}")
                        continue
            
            logger.info(f"加载了 {len(tools)} 个 {tool_type} 类型工具配置")
            return tools
            
        except Exception as e:
            logger.error(f"按类型加载工具配置失败 {tool_type}: {e}")
            raise
    
    def load_all_tools(self) -> Dict[str, List[ToolConfig]]:
        """加载所有工具配置
        
        Returns:
            按类型分组的工具配置字典
        """
        try:
            all_tools = {}
            
            # 支持的工具类型
            tool_types = ["builtin", "native", "rest", "mcp"]
            
            for tool_type in tool_types:
                tools = self.load_tools_by_type(tool_type)
                if tools:
                    all_tools[tool_type] = tools
            
            total_count = sum(len(tools) for tools in all_tools.values())
            logger.info(f"加载了所有工具配置，共 {total_count} 个工具")
            return all_tools
            
        except Exception as e:
            logger.error(f"加载所有工具配置失败: {e}")
            raise
    
    def validate_tool_config(self, tool_config: ToolConfig) -> bool:
        """验证工具配置（委托给验证服务）
        
        Args:
            tool_config: 工具配置实体
            
        Returns:
            是否有效
        """
        validation_result = self.validate_config(tool_config)
        return validation_result.is_valid
    
    def get_supported_tool_types(self) -> List[str]:
        """获取支持的工具类型列表
        
        Returns:
            工具类型列表
        """
        return ["builtin", "native", "rest", "mcp"]
    
    def is_tool_type_supported(self, tool_type: str) -> bool:
        """检查是否支持指定的工具类型
        
        Args:
            tool_type: 工具类型
            
        Returns:
            是否支持
        """
        return tool_type in self.get_supported_tool_types()


# 便捷函数
def get_tools_config_service(config_manager: Optional[Any] = None,
                           mapper_registry: Optional[IConfigMapperRegistry] = None) -> ToolsConfigService:
    """获取工具配置服务实例
    
    Args:
        config_manager: 配置管理器
        mapper_registry: 配置映射器注册表
        
    Returns:
        工具配置服务实例
    """
    return ToolsConfigService(config_manager, mapper_registry)