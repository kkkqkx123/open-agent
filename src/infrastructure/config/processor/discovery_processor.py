"""配置发现处理器

提供配置文件的自动发现功能，专注于发现逻辑，不包含加载和处理。
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Protocol
from dataclasses import dataclass

from .base_processor import BaseConfigProcessor
from ..loader import ConfigLoader
from src.interfaces.dependency_injection import get_logger

logger = get_logger(__name__)


@dataclass
class ConfigFileInfo:
    """配置文件信息"""
    path: Path
    config_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DiscoveryStrategy(Protocol):
    """配置发现策略协议"""
    
    def discover_files(self, config_dir: Path) -> List[ConfigFileInfo]:
        """发现配置文件"""
        ...
    
    def get_file_hierarchy(self, files: List[ConfigFileInfo]) -> Dict[str, List[ConfigFileInfo]]:
        """获取文件层次结构"""
        ...


class DefaultDiscoveryStrategy:
    """默认配置发现策略"""
    
    def __init__(self, supported_extensions: Optional[List[str]] = None):
        """初始化默认发现策略"""
        self.supported_extensions = supported_extensions or ['.yaml', '.yml', '.json']
        logger.debug("默认配置发现策略初始化完成")
    
    def discover_files(self, config_dir: Path) -> List[ConfigFileInfo]:
        """发现配置文件"""
        files: List[ConfigFileInfo] = []
        
        if not config_dir.exists():
            logger.warning(f"配置目录不存在: {config_dir}")
            return files
        
        # 遍历配置目录
        for config_file in config_dir.rglob("*"):
            if config_file.suffix.lower() in self.supported_extensions:
                file_info = ConfigFileInfo(
                    path=config_file,
                    config_type=self._determine_file_type(config_file, config_dir),
                    metadata=self._extract_metadata(config_file)
                )
                files.append(file_info)
        
        logger.debug(f"发现 {len(files)} 个配置文件")
        return files
    
    def _determine_file_type(self, config_file: Path, config_dir: Path) -> Optional[str]:
        """确定文件类型"""
        path_parts = config_file.relative_to(config_dir).parts
        
        if len(path_parts) == 1 and path_parts[0].startswith("global"):
            return "global"
        elif len(path_parts) >= 2:
            return path_parts[0]  # 第一级目录作为类型
        else:
            return "other"
    
    def _extract_metadata(self, config_file: Path) -> Dict[str, Any]:
        """提取文件元数据"""
        return {
            "size": config_file.stat().st_size if config_file.exists() else 0,
            "modified": config_file.stat().st_mtime if config_file.exists() else 0
        }
    
    def get_file_hierarchy(self, files: List[ConfigFileInfo]) -> Dict[str, List[ConfigFileInfo]]:
        """获取文件层次结构"""
        hierarchy: Dict[str, List[ConfigFileInfo]] = {}
        
        for file_info in files:
            config_type = file_info.config_type or "other"
            if config_type not in hierarchy:
                hierarchy[config_type] = []
            hierarchy[config_type].append(file_info)
        
        return hierarchy


class DiscoveryProcessor(BaseConfigProcessor):
    """配置发现处理器
    
    专注于配置文件的发现功能，不包含加载和处理逻辑。
    """
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None,
                 strategy: Optional[DiscoveryStrategy] = None,
                 config_loader: Optional[ConfigLoader] = None):
        """初始化配置发现处理器
        
        Args:
            config_dir: 配置目录路径
            strategy: 发现策略
            config_loader: 配置加载器（可选，用于加载配置）
        """
        super().__init__("discovery")
        
        if config_dir is None:
            config_dir = Path("configs")
        elif isinstance(config_dir, str):
            config_dir = Path(config_dir)
        
        self.config_dir = config_dir
        self.strategy = strategy or DefaultDiscoveryStrategy()
        self.config_loader = config_loader
        
        # 缓存
        self._discovered_files: List[ConfigFileInfo] = []
        
        logger.debug(f"配置发现处理器初始化完成，配置目录: {self.config_dir}")
    
    def _process_internal(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """内部处理逻辑
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        # 发现处理器主要用于发现配置，而不是处理单个配置
        return config
    
    def discover_files(self, force_refresh: bool = False) -> List[ConfigFileInfo]:
        """发现配置文件
        
        Args:
            force_refresh: 是否强制刷新缓存
            
        Returns:
            List[ConfigFileInfo]: 配置文件信息列表
        """
        if not force_refresh and self._discovered_files:
            return self._discovered_files
        
        files = self.strategy.discover_files(self.config_dir)
        self._discovered_files = files
        
        return files
    
    def get_file_hierarchy(self) -> Dict[str, List[ConfigFileInfo]]:
        """获取配置文件层次结构
        
        Returns:
            Dict[str, List[ConfigFileInfo]]: 按类型分组的配置文件信息
        """
        files = self.discover_files()
        return self.strategy.get_file_hierarchy(files)
    
    def load_config(self, config_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 配置数据
        """
        if not self.config_loader:
            logger.warning("未配置配置加载器，无法加载配置文件")
            return None
        
        if isinstance(config_path, str):
            config_path = Path(config_path)
        
        try:
            return self.config_loader.load(str(config_path))
        except Exception as e:
            logger.error(f"加载配置文件失败 {config_path}: {e}")
            return None
    
    def reload_files(self) -> None:
        """重新加载配置文件列表"""
        self._discovered_files.clear()
        logger.info("配置文件列表已清除")
    
    def validate_directory_structure(self) -> Dict[str, List[str]]:
        """验证配置目录结构
        
        Returns:
            Dict[str, List[str]]: 验证结果，包含错误和警告信息
        """
        result = {
            "errors": [],
            "warnings": []
        }
        
        if not self.config_dir.exists():
            result["errors"].append(f"配置目录不存在: {self.config_dir}")
            return result
        
        # 检查是否为空目录
        files = list(self.config_dir.rglob("*"))
        config_files = [f for f in files if f.suffix.lower() in ['.yaml', '.yml', '.json']]
        
        if not config_files:
            result["warnings"].append("配置目录中没有找到配置文件")
        
        return result