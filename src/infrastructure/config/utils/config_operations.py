"""配置操作工具

专门用于配置系统的操作功能。
"""

import json
from typing import Dict, Any
from pathlib import Path
from datetime import datetime

from ..config_system import IConfigSystem
from ...exceptions import ConfigurationError


class ConfigOperations:
    """配置操作器 - 提供实用工具功能
    
    专注于配置的导出、摘要等高级功能，不与ConfigSystem的核心功能重叠。
    """
    
    def __init__(self, config_system: IConfigSystem):
        """初始化配置操作器
        
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
    
    def validate_all_configs(self) -> Dict[str, Any]:
        """验证所有配置
        
        Returns:
            验证结果
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "validations": {}
        }
        
        try:
            # 验证全局配置
            try:
                self._config_system.load_global_config()
                results["validations"]["global"] = {"status": "valid"}
            except Exception as e:
                results["validations"]["global"] = {"status": "invalid", "error": str(e)}
            
            # 验证LLM配置
            llm_configs = self._config_system.list_configs("llms")
            results["validations"]["llms"] = {}
            for config_name in llm_configs:
                try:
                    self._config_system.load_llm_config(config_name)
                    results["validations"]["llms"][config_name] = {"status": "valid"}
                except Exception as e:
                    results["validations"]["llms"][config_name] = {"status": "invalid", "error": str(e)}
            
            # 验证工具配置
            tool_configs = self._config_system.list_configs("tool-sets")
            results["validations"]["tools"] = {}
            for config_name in tool_configs:
                try:
                    self._config_system.load_tool_config(config_name)
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
        dependencies = {
            "timestamp": datetime.now().isoformat(),
            "dependencies": {}
        }
        
        try:
            # 分析LLM配置的依赖关系
            llm_configs = self._config_system.list_configs("llms")
            dependencies["dependencies"]["llms"] = {}
            
            for config_name in llm_configs:
                config = self._config_system.load_llm_config(config_name)
                config_deps = []
                
                # 检查组配置依赖
                if hasattr(config, 'group') and config.group:
                    config_deps.append(f"group:{config.group}")
                
                # 检查token_counter依赖
                if hasattr(config, 'token_counter') and config.token_counter:
                    config_deps.append(f"token_counter:{config.token_counter}")
                
                dependencies["dependencies"]["llms"][config_name] = config_deps
            
            # 分析工具配置的依赖关系
            tool_configs = self._config_system.list_configs("tool-sets")
            dependencies["dependencies"]["tools"] = {}
            
            for config_name in tool_configs:
                config = self._config_system.load_tool_config(config_name)
                config_deps = []
                
                # 检查组配置依赖
                if hasattr(config, 'group') and config.group:
                    config_deps.append(f"group:{config.group}")
                
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
                config1 = self._config_system.load_llm_config(config_name1)
                config2 = self._config_system.load_llm_config(config_name2)
            elif config_type == "tool-sets":
                config1 = self._config_system.load_tool_config(config_name1)
                config2 = self._config_system.load_tool_config(config_name2)
            else:
                raise ValueError(f"不支持的配置类型: {config_type}")
            
            # 转换为字典进行比较
            dict1 = config1.dict()
            dict2 = config2.dict()
            
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