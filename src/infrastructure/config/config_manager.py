"""配置管理器

提供高级配置管理功能，作为配置系统的补充。
"""

import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from .config_system import IConfigSystem
from .processor.validator import ValidationResult
from ..exceptions import ConfigurationError


class ConfigManager:
    """配置管理器
    
    提供高级配置管理功能，包括配置快照、批量操作等。
    """
    
    def __init__(self, config_system: IConfigSystem):
        """初始化配置管理器
        
        Args:
            config_system: 配置系统实例
        """
        self._config_system = config_system
    
    def get_config_with_fallback(
        self, 
        config_type: str, 
        name: str, 
        fallback: Any
    ) -> Any:
        """获取配置，支持回退值
        
        Args:
            config_type: 配置类型
            name: 配置名称
            fallback: 回退值
            
        Returns:
            配置值或回退值
        """
        try:
            if config_type == "global":
                return self._config_system.load_global_config()
            elif config_type == "llm":
                return self._config_system.load_llm_config(name)
            elif config_type == "tool":
                return self._config_system.load_tool_config(name)
            elif config_type == "token_counter":
                return self._config_system.load_token_counter_config(name)
            else:
                return fallback
        except Exception:
            return fallback
    
    def reload_and_validate(self) -> ValidationResult:
        """重新加载并验证所有配置
        
        Returns:
            验证结果
        """
        result = ValidationResult(True)
        
        try:
            # 重新加载配置
            self._config_system.reload_configs()
            
            # 验证全局配置
            try:
                self._config_system.load_global_config()
            except Exception as e:
                result.add_error(f"全局配置验证失败: {e}")
            
            # 验证LLM配置
            try:
                llm_configs = self._config_system.list_configs("llms")
                for config_name in llm_configs:
                    self._config_system.load_llm_config(config_name)
            except Exception as e:
                result.add_error(f"LLM配置验证失败: {e}")
            
            # 验证工具配置
            try:
                tool_configs = self._config_system.list_configs("tool-sets")
                for config_name in tool_configs:
                    self._config_system.load_tool_config(config_name)
            except Exception as e:
                result.add_error(f"工具配置验证失败: {e}")
                
        except Exception as e:
            result.add_error(f"重新加载配置失败: {e}")
        
        return result
    
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
    
    def import_config_snapshot(self, input_path: str, overwrite: bool = False) -> None:
        """导入配置快照
        
        Args:
            input_path: 输入文件路径
            overwrite: 是否覆盖现有配置
        """
        # 注意：这是一个简化实现，实际应用中需要更复杂的逻辑
        # 来处理配置导入和验证
        
        input_file = Path(input_path)
        if not input_file.exists():
            raise ConfigurationError(f"配置快照文件不存在: {input_path}")
        
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                snapshot = json.load(f)
            
            # 验证快照格式
            if "configs" not in snapshot:
                raise ConfigurationError("无效的配置快照格式")
            
            # 这里可以添加实际的配置导入逻辑
            # 由于配置系统当前不支持写入，这里只是一个占位符
            
            raise ConfigurationError("配置导入功能尚未实现")
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"配置快照文件格式错误: {e}")
        except Exception as e:
            raise ConfigurationError(f"导入配置快照失败: {e}")
    
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
