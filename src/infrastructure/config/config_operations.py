"""配置管理器

提供高级配置管理功能，作为配置系统的补充。
"""

import json
from typing import Dict, Any
from pathlib import Path
from datetime import datetime

from .config_system import IConfigSystem
from ..exceptions import ConfigurationError


class ConfigOperations:
    """配置管理器 - 提供实用工具功能
    
    专注于配置的导出、摘要等高级功能，不与ConfigSystem的核心功能重叠。
    """
    
    def __init__(self, config_system: IConfigSystem):
        """初始化配置管理器
        
        Args:
            config_system: 配置系统实例
        """
        self._config_system = config_system
    
    def export_config_snapshot(self, output_path: str) -> None:
        """导出配置快照
        
        Args:
            output_path: 输出文件路径
        """
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "configs": {}
        }
        
        try:
            # 导出全局配置
            global_config = self._config_system.load_global_config()
            snapshot["configs"]["global"] = global_config.dict()
            
            # 导出LLM配置
            llm_configs = self._config_system.list_configs("llms")
            snapshot["configs"]["llms"] = {}
            for config_name in llm_configs:
                config = self._config_system.load_llm_config(config_name)
                snapshot["configs"]["llms"][config_name] = config.dict()
            
            # 导出工具配置
            tool_configs = self._config_system.list_configs("tool-sets")
            snapshot["configs"]["tools"] = {}
            for config_name in tool_configs:
                config = self._config_system.load_tool_config(config_name)
                snapshot["configs"]["tools"][config_name] = config.dict()
            
            # 写入文件
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise ConfigurationError(f"导出配置快照失败: {e}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要信息
        
        Returns:
            配置摘要
        """
        summary = {
            "timestamp": datetime.now().isoformat(),
            "config_counts": {}
        }
        
        try:
            # 统计各种配置的数量
            summary["config_counts"]["llms"] = len(self._config_system.list_configs("llms"))
            summary["config_counts"]["tools"] = len(self._config_system.list_configs("tool-sets"))
            
            # 获取全局配置信息
            global_config = self._config_system.load_global_config()
            summary["environment"] = global_config.env
            summary["debug"] = global_config.debug
            
        except Exception as e:
            summary["error"] = str(e)
        
        return summary