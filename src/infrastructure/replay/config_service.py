"""重放功能配置服务"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from src.domain.replay.config import ReplayConfig, ReplayMode

logger = logging.getLogger(__name__)


class ReplayConfigService:
    """重放配置服务"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """初始化配置服务
        
        Args:
            config_path: 配置文件路径，默认为 configs/history/replay.yaml
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "configs" / "history" / "replay.yaml"
        
        self.config_path = config_path
        self._config: Optional[ReplayConfig] = None
    
    def get_config(self) -> ReplayConfig:
        """获取重放配置
        
        Returns:
            ReplayConfig: 重放配置对象
        """
        if self._config is None:
            self._load_config()
        assert self._config is not None
        return self._config
    
    def is_enabled(self) -> bool:
        """检查重放功能是否启用
        
        Returns:
            bool: 是否启用
        """
        config = self.get_config()
        return getattr(config, "enabled", True)
    
    def get_processor_config(self) -> Dict[str, Any]:
        """获取处理器配置
        
        Returns:
            Dict[str, Any]: 处理器配置字典
        """
        config = self.get_config()
        return {
            "max_concurrent_replays": getattr(config, "max_concurrent_replays", 10),
            "session_timeout": getattr(config, "session_timeout", 3600)
        }
    
    def get_mode_config(self, mode: str) -> Dict[str, Any]:
        """获取指定模式的配置
        
        Args:
            mode: 重放模式名称
            
        Returns:
            Dict[str, Any]: 模式配置字典
        """
        config = self.get_config()
        modes = getattr(config, "modes", {})
        return modes.get(mode, {})
    
    def get_analyzer_config(self) -> Dict[str, Any]:
        """获取分析器配置
        
        Returns:
            Dict[str, Any]: 分析器配置字典
        """
        config = self.get_config()
        return {
            "enable_statistics": getattr(config, "enable_statistics", True),
            "enable_performance_analysis": getattr(config, "enable_performance_analysis", True),
            "enable_cost_analysis": getattr(config, "enable_cost_analysis", True),
            "enable_error_analysis": getattr(config, "enable_error_analysis", True),
            "cache_ttl": getattr(config, "cache_ttl", 3600),
            "max_analysis_history": getattr(config, "max_analysis_history", 100)
        }
    
    def _load_config(self) -> None:
        """加载配置"""
        try:
            # 构建默认的ReplayConfig
            self._config = ReplayConfig()
            logger.debug(f"重放配置加载成功: {self.config_path}")
        except Exception as e:
            logger.error(f"加载重放配置失败: {e}")
            # 使用默认配置
            self._config = ReplayConfig()
            logger.warning("使用默认重放配置")
    
    def reload_config(self) -> None:
        """重新加载配置"""
        self._config = None
        self._load_config()
