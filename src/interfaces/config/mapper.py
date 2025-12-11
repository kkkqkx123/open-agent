"""配置映射器接口定义

定义配置数据和业务实体之间的映射接口，支持统一配置系统。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..common_domain import ValidationResult


class IConfigMapper(ABC):
    """配置映射器接口
    
    负责在配置数据和业务实体之间进行转换。
    """
    
    @abstractmethod
    def dict_to_entity(self, config_data: Dict[str, Any]) -> Any:
        """将配置字典转换为业务实体
        
        Args:
            config_data: 配置字典数据
            
        Returns:
            Any: 业务实体实例
        """
        pass
    
    @abstractmethod
    def entity_to_dict(self, entity: Any) -> Dict[str, Any]:
        """将业务实体转换为配置字典
        
        Args:
            entity: 业务实体实例
            
        Returns:
            Dict[str, Any]: 配置字典数据
        """
        pass
    
    @abstractmethod
    def validate_config(self, config_data: Dict[str, Any]) -> ValidationResult:
        """验证配置数据
        
        Args:
            config_data: 配置字典数据
            
        Returns:
            ValidationResult: 验证结果
        """
        pass


class IModuleConfigService(ABC):
    """模块配置服务接口
    
    提供模块特定的配置管理服务。
    """
    
    @abstractmethod
    def load_config(self, config_path: str) -> Any:
        """加载模块配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Any: 配置实体
        """
        pass
    
    @abstractmethod
    def save_config(self, config: Any, config_path: str) -> None:
        """保存模块配置
        
        Args:
            config: 配置实体
            config_path: 配置文件路径
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Any) -> ValidationResult:
        """验证模块配置
        
        Args:
            config: 配置实体
            
        Returns:
            ValidationResult: 验证结果
        """
        pass


class IModuleConfigRegistry(ABC):
    """模块配置注册表接口
    
    管理模块配置的注册和获取。
    """
    
    @abstractmethod
    def register_module(self, module_type: str, config: 'ModuleConfig') -> None:
        """注册模块配置
        
        Args:
            module_type: 模块类型
            config: 模块配置
        """
        pass
    
    @abstractmethod
    def get_module_config(self, module_type: str) -> Optional['ModuleConfig']:
        """获取模块配置
        
        Args:
            module_type: 模块类型
            
        Returns:
            Optional[ModuleConfig]: 模块配置，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def post_process(self, module_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """模块特定后处理
        
        Args:
            module_type: 模块类型
            config: 配置数据
            
        Returns:
            Dict[str, Any]: 处理后的配置数据
        """
        pass


class IConfigMapperRegistry(ABC):
    """配置映射器注册表接口
    
    管理配置映射器的注册和获取。
    """
    
    @abstractmethod
    def register_mapper(self, module_type: str, mapper: IConfigMapper) -> None:
        """注册配置映射器
        
        Args:
            module_type: 模块类型
            mapper: 配置映射器
        """
        pass
    
    @abstractmethod
    def get_mapper(self, module_type: str) -> Optional[IConfigMapper]:
        """获取配置映射器
        
        Args:
            module_type: 模块类型
            
        Returns:
            Optional[IConfigMapper]: 配置映射器，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def dict_to_entity(self, module_type: str, config_data: Dict[str, Any]) -> Any:
        """将配置字典转换为业务实体
        
        Args:
            module_type: 模块类型
            config_data: 配置字典数据
            
        Returns:
            Any: 业务实体实例
        """
        pass
    
    @abstractmethod
    def entity_to_dict(self, module_type: str, entity: Any) -> Dict[str, Any]:
        """将业务实体转换为配置字典
        
        Args:
            module_type: 模块类型
            entity: 业务实体实例
            
        Returns:
            Dict[str, Any]: 配置字典数据
        """
        pass


class ICrossModuleResolver(ABC):
    """跨模块引用解析器接口
    
    解析配置中的跨模块引用。
    """
    
    @abstractmethod
    def resolve(self, module_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析跨模块引用
        
        Args:
            module_type: 模块类型
            config: 配置数据
            
        Returns:
            Dict[str, Any]: 解析后的配置数据
        """
        pass


class IModuleConfigLoader(ABC):
    """模块配置加载器接口
    
    提供模块特定的配置加载功能。
    """
    
    @abstractmethod
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        pass


class IUnifiedConfigService(ABC):
    """统一配置服务接口
    
    提供所有模块配置的统一入口。
    """
    
    @abstractmethod
    def load_module_config(self, module_type: str, config_path: str) -> Any:
        """加载模块配置
        
        Args:
            module_type: 模块类型
            config_path: 配置文件路径
            
        Returns:
            Any: 配置实体
        """
        pass
    
    @abstractmethod
    def save_module_config(self, module_type: str, config: Any, config_path: str) -> None:
        """保存模块配置
        
        Args:
            module_type: 模块类型
            config: 配置实体
            config_path: 配置文件路径
        """
        pass
    
    @abstractmethod
    def validate_module_config(self, module_type: str, config: Any) -> ValidationResult:
        """验证模块配置
        
        Args:
            module_type: 模块类型
            config: 配置实体
            
        Returns:
            ValidationResult: 验证结果
        """
        pass


# 模块配置数据类
from dataclasses import dataclass
from typing import List, Callable, Optional


@dataclass
class ModuleConfig:
    """模块配置定义
    
    定义模块的配置元数据和处理逻辑。
    """
    module_type: str
    name: str
    description: str
    processors: List[str]
    validator: Optional[str] = None
    post_processor: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    dependencies: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class ModuleDependency:
    """模块依赖定义
    
    定义模块间的依赖关系。
    """
    module_type: str
    config_path: str
    required_fields: List[str]
    optional_fields: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.optional_fields is None:
            self.optional_fields = []


@dataclass
class ConfigChangeEvent:
    """配置变更事件
    
    描述配置变更事件的信息。
    """
    module_type: str
    config_path: str
    new_config: Dict[str, Any]
    old_config: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None


class IConfigChangeListener(ABC):
    """配置变更监听器接口
    
    监听配置变更事件。
    """
    
    @abstractmethod
    def on_config_changed(self, event: ConfigChangeEvent) -> None:
        """配置变更处理
        
        Args:
            event: 配置变更事件
        """
        pass


class IConfigWatcher(ABC):
    """配置监听器接口
    
    监听配置文件变更。
    """
    
    @abstractmethod
    def start(self) -> None:
        """开始监听"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """停止监听"""
        pass
    
    @abstractmethod
    def add_change_listener(self, listener: Callable[[], None]) -> None:
        """添加变更监听器
        
        Args:
            listener: 变更监听器
        """
        pass


class IConfigMonitor(ABC):
    """配置监控器接口
    
    监控配置文件变更并触发重载。
    """
    
    @abstractmethod
    def start_watching(self, module_type: str, config_path: str) -> None:
        """开始监控配置文件
        
        Args:
            module_type: 模块类型
            config_path: 配置文件路径
        """
        pass
    
    @abstractmethod
    def add_change_listener(self, listener: IConfigChangeListener) -> None:
        """添加配置变更监听器
        
        Args:
            listener: 配置变更监听器
        """
        pass


@dataclass
class ConfigVersion:
    """配置版本信息
    
    描述配置的版本信息。
    """
    module_type: str
    config_path: str
    version: str
    config: Dict[str, Any]
    comment: str = ""
    timestamp: Optional[str] = None


class IConfigVersionManager(ABC):
    """配置版本管理器接口
    
    管理配置的版本控制和回滚。
    """
    
    @abstractmethod
    def save_version(self, module_type: str, config_path: str, config: Dict[str, Any], 
                    version: str, comment: str = "") -> None:
        """保存配置版本
        
        Args:
            module_type: 模块类型
            config_path: 配置文件路径
            config: 配置数据
            version: 版本号
            comment: 版本注释
        """
        pass
    
    @abstractmethod
    def load_version(self, module_type: str, config_path: str, version: str) -> Dict[str, Any]:
        """加载指定版本的配置
        
        Args:
            module_type: 模块类型
            config_path: 配置文件路径
            version: 版本号
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        pass
    
    @abstractmethod
    def list_versions(self, module_type: str, config_path: str) -> List[ConfigVersion]:
        """列出配置版本
        
        Args:
            module_type: 模块类型
            config_path: 配置文件路径
            
        Returns:
            List[ConfigVersion]: 版本列表
        """
        pass
    
    @abstractmethod
    def rollback(self, module_type: str, config_path: str, version: str) -> None:
        """回滚到指定版本
        
        Args:
            module_type: 模块类型
            config_path: 配置文件路径
            version: 版本号
        """
        pass


class IConfigStorage(ABC):
    """配置存储接口
    
    提供配置的持久化存储。
    """
    
    @abstractmethod
    def save_version(self, version_info: ConfigVersion) -> None:
        """保存版本信息
        
        Args:
            version_info: 版本信息
        """
        pass
    
    @abstractmethod
    def load_version(self, module_type: str, config_path: str, version: str) -> ConfigVersion:
        """加载版本信息
        
        Args:
            module_type: 模块类型
            config_path: 配置文件路径
            version: 版本号
            
        Returns:
            ConfigVersion: 版本信息
        """
        pass
    
    @abstractmethod
    def list_versions(self, module_type: str, config_path: str) -> List[ConfigVersion]:
        """列出版本信息
        
        Args:
            module_type: 模块类型
            config_path: 配置文件路径
            
        Returns:
            List[ConfigVersion]: 版本列表
        """
        pass