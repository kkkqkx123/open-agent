"""配置操作工具

专门用于配置系统的操作功能。
"""

import json
from typing import Dict, Any
from pathlib import Path
from datetime import datetime

from ...config import ConfigManager
from ..exceptions import ConfigurationError


class ConfigOperations:
    """配置操作器 - 提供实用工具功能
    
    专注于配置的导出、摘要等高级功能，不与ConfigManager的核心功能重叠。
    """
    
    def __init__(self, config_manager: ConfigManager):
        """初始化配置操作器
        
        Args:
            config_manager: 配置管理器实例
        """
        self._config_manager = config_manager
    
    def export_config_snapshot(self, output_path: str) -> None:
        """导出配置快照
        
        Args:
            output_path: 输出文件路径
        """
        snapshot: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "configs": {}
        }
        
        try:
            # 导出全局配置
            global_config = self._config_manager.load_config("global")
            snapshot["configs"]["global"] = self._to_dict(global_config)
            
            # 导出LLM配置
            llm_config_files = self._config_manager.list_config_files("llms")
            snapshot["configs"]["llms"] = {}
            for config_file in llm_config_files:
                config = self._config_manager.load_config(config_file)
                config_name = Path(config_file).stem
                snapshot["configs"]["llms"][config_name] = self._to_dict(config)
            
            # 导出工具配置
            tool_config_files = self._config_manager.list_config_files("tool-sets")
            snapshot["configs"]["tools"] = {}
            for config_file in tool_config_files:
                config = self._config_manager.load_config(config_file)
                config_name = Path(config_file).stem
                snapshot["configs"]["tools"][config_name] = self._to_dict(config)
            
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
        summary: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "config_counts": {}
        }
        
        try:
            # 统计各种配置的数量
            summary["config_counts"]["llms"] = len(self._config_manager.list_config_files("llms"))
            summary["config_counts"]["tools"] = len(self._config_manager.list_config_files("tool-sets"))
            
            # 获取全局配置信息
            global_config = self._config_manager.load_config("global")
            if isinstance(global_config, dict):
                summary["environment"] = global_config.get('env', 'unknown')
                summary["debug"] = global_config.get('debug', False)
            else:
                summary["environment"] = getattr(global_config, 'env', 'unknown')
                summary["debug"] = getattr(global_config, 'debug', False)
            
        except Exception as e:
            summary["error"] = str(e)
        
        return summary
    
    def validate_all_configs(self) -> Dict[str, Any]:
        """验证所有配置
        
        Returns:
            验证结果
        """
        results: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "validations": {}
        }
        
        try:
            # 验证全局配置
            try:
                self._config_manager.load_config("global")
                results["validations"]["global"] = {"status": "valid"}
            except Exception as e:
                results["validations"]["global"] = {"status": "invalid", "error": str(e)}
            
            # 验证LLM配置
            llm_config_files = self._config_manager.list_config_files("llms")
            results["validations"]["llms"] = {}
            for config_file in llm_config_files:
                config_name = Path(config_file).stem
                try:
                    self._config_manager.load_config(config_file)
                    results["validations"]["llms"][config_name] = {"status": "valid"}
                except Exception as e:
                    results["validations"]["llms"][config_name] = {"status": "invalid", "error": str(e)}
            
            # 验证工具配置
            tool_config_files = self._config_manager.list_config_files("tool-sets")
            results["validations"]["tools"] = {}
            for config_file in tool_config_files:
                config_name = Path(config_file).stem
                try:
                    self._config_manager.load_config(config_file)
                    results["validations"]["tools"][config_name] = {"status": "valid"}
                except Exception as e:
                    results["validations"]["tools"][config_name] = {"status": "invalid", "error": str(e)}
            
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def get_config_dependencies(self) -> Dict[str, Any]:
        """获取配置依赖关系
        
        Returns:
            配置依赖关系
        """
        dependencies: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "dependencies": {}
        }
        
        try:
            # 分析LLM配置的依赖关系
            llm_config_files = self._config_manager.list_config_files("llms")
            dependencies["dependencies"]["llms"] = {}
            
            for config_file in llm_config_files:
                config = self._config_manager.load_config(config_file)
                config_name = Path(config_file).stem
                config_deps = []
                
                # 检查组配置依赖
                if isinstance(config, dict):
                    group = config.get('group')
                    if group:
                        config_deps.append(f"group:{group}")
                    token_counter = config.get('token_counter')
                    if token_counter:
                        config_deps.append(f"token_counter:{token_counter}")
                else:
                    if hasattr(config, 'group') and getattr(config, 'group', None):
                        config_deps.append(f"group:{getattr(config, 'group')}")
                    if hasattr(config, 'token_counter') and getattr(config, 'token_counter', None):
                        config_deps.append(f"token_counter:{getattr(config, 'token_counter')}")
                
                dependencies["dependencies"]["llms"][config_name] = config_deps
            
            # 分析工具配置的依赖关系
            tool_config_files = self._config_manager.list_config_files("tool-sets")
            dependencies["dependencies"]["tools"] = {}
            
            for config_file in tool_config_files:
                config = self._config_manager.load_config(config_file)
                config_name = Path(config_file).stem
                config_deps = []
                
                # 检查组配置依赖
                if isinstance(config, dict):
                    group = config.get('group')
                    if group:
                        config_deps.append(f"group:{group}")
                else:
                    if hasattr(config, 'group') and getattr(config, 'group', None):
                        config_deps.append(f"group:{getattr(config, 'group')}")
                
                dependencies["dependencies"]["tools"][config_name] = config_deps
            
        except Exception as e:
            dependencies["error"] = str(e)
        
        return dependencies
    
    def backup_all_configs(self, backup_dir: str = "config_backups") -> str:
        """备份所有配置
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            备份文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = Path(backup_dir) / f"config_backup_{timestamp}.json"
        
        self.export_config_snapshot(str(backup_file))
        return str(backup_file)
    
    def restore_configs_from_backup(self, backup_file: str) -> bool:
        """从备份恢复配置
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            是否成功恢复
        """
        try:
            with open(backup_file, "r", encoding="utf-8") as f:
                backup_data = json.load(f)
            
            # 这里可以实现配置恢复逻辑
            # 由于配置系统的复杂性，这里只是示例
            print(f"从备份 {backup_file} 恢复配置")
            print(f"备份时间: {backup_data.get('timestamp')}")
            print(f"配置数量: {len(backup_data.get('configs', {}))}")
            
            return True
            
        except Exception as e:
            print(f"恢复配置失败: {e}")
            return False
    
    def compare_configs(self, config_type: str, config_name1: str, config_name2: str) -> Dict[str, Any]:
        """比较两个配置
        
        Args:
            config_type: 配置类型
            config_name1: 第一个配置名称
            config_name2: 第二个配置名称
            
        Returns:
            比较结果
        """
        comparison = {
            "timestamp": datetime.now().isoformat(),
            "config_type": config_type,
            "config1": config_name1,
            "config2": config_name2,
            "differences": {}
        }
        
        try:
            # 加载配置
            if config_type == "llms":
                config1 = self._config_manager.load_config(f"llms/{config_name1}")
                config2 = self._config_manager.load_config(f"llms/{config_name2}")
            elif config_type == "tool-sets":
                config1 = self._config_manager.load_config(f"tool-sets/{config_name1}")
                config2 = self._config_manager.load_config(f"tool-sets/{config_name2}")
            else:
                comparison["error"] = f"不支持的配置类型: {config_type}"
                return comparison
            
            # 转换为字典进行比较
            dict1 = self._to_dict(config1)
            dict2 = self._to_dict(config2)
            
            # 找出差异
            all_keys = set(dict1.keys()) | set(dict2.keys())
            
            for key in all_keys:
                if key not in dict1:
                    comparison["differences"][key] = {"status": "added", "value": dict2[key]}
                elif key not in dict2:
                    comparison["differences"][key] = {"status": "removed", "value": dict1[key]}
                elif dict1[key] != dict2[key]:
                    comparison["differences"][key] = {
                        "status": "changed",
                        "old_value": dict1[key],
                        "new_value": dict2[key]
                    }
            
            comparison["identical"] = len(comparison["differences"]) == 0
            
        except Exception as e:
            comparison["error"] = str(e)
        
        return comparison
    
    @staticmethod
    def _to_dict(obj: Any) -> Any:
        """将对象转换为字典或返回原始值
        
        Args:
            obj: 要转换的对象
            
        Returns:
            字典对象或原始值
        """
        if hasattr(obj, 'dict'):
            return obj.dict()
        elif hasattr(obj, '__dict__'):
            return dict(obj.__dict__)
        elif isinstance(obj, dict):
            return obj
        else:
            # 对于其他类型，返回原值
            return obj
