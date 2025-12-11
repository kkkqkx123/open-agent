"""配置发现管理器实现

提供配置系统的发现管理功能，包括配置文件发现、依赖分析和监听。
"""

from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import logging
import os
import yaml
from datetime import datetime

from src.interfaces.config.loader import IConfigLoader

logger = logging.getLogger(__name__)


class DiscoveryManager:
    """配置发现管理器
    
    提供配置系统的发现管理功能，包括配置文件发现、依赖分析和监听。
    """
    
    def __init__(self, config_loader: Optional[IConfigLoader] = None, base_path: str = "configs"):
        """初始化发现管理器
        
        Args:
            config_loader: 配置加载器
            base_path: 基础配置路径
        """
        self.config_loader = config_loader
        self.base_path = Path(base_path)
        self._watchers: Dict[str, Callable] = {}
        
        logger.debug(f"初始化配置发现管理器，基础路径: {base_path}")
    
    def discover_configs(self, pattern: str = "*", base_path: Optional[str] = None) -> List[str]:
        """发现配置文件
        
        Args:
            pattern: 文件模式（支持通配符）
            base_path: 基础路径，如果为None则使用默认路径
            
        Returns:
            配置文件路径列表
        """
        try:
            search_path = Path(base_path) if base_path else self.base_path
            
            if not search_path.exists():
                logger.warning(f"配置路径不存在: {search_path}")
                return []
            
            config_files = []
            
            # 搜索YAML文件
            for file_path in search_path.rglob(f"{pattern}.yaml"):
                if file_path.is_file():
                    config_files.append(str(file_path))
            
            for file_path in search_path.rglob(f"{pattern}.yml"):
                if file_path.is_file():
                    config_files.append(str(file_path))
            
            # 排序并返回
            config_files.sort()
            logger.debug(f"发现 {len(config_files)} 个配置文件，模式: {pattern}")
            
            return config_files
            
        except Exception as e:
            logger.error(f"发现配置文件失败: {e}")
            return []
    
    def discover_module_configs(self, module_type: str, pattern: str = "*") -> List[str]:
        """发现模块特定配置文件
        
        Args:
            module_type: 模块类型
            pattern: 文件模式（支持通配符）
            
        Returns:
            配置文件路径列表
        """
        try:
            module_path = self.base_path / module_type
            
            if not module_path.exists():
                logger.debug(f"模块配置路径不存在: {module_path}")
                return []
            
            config_files = []
            
            # 对于LLM模块，需要特殊处理provider目录结构
            if module_type == "llm":
                config_files.extend(self._discover_llm_configs(module_path, pattern))
            else:
                # 搜索模块特定的YAML文件
                for file_path in module_path.glob(f"{pattern}.yaml"):
                    if file_path.is_file():
                        config_files.append(str(file_path))
                
                for file_path in module_path.glob(f"{pattern}.yml"):
                    if file_path.is_file():
                        config_files.append(str(file_path))
            
            # 排序并返回
            config_files.sort()
            logger.debug(f"发现 {len(config_files)} 个 {module_type} 模块配置文件")
            
            return config_files
            
        except Exception as e:
            logger.error(f"发现模块配置文件失败 {module_type}: {e}")
            return []
    
    def _discover_llm_configs(self, llm_path: Path, pattern: str) -> List[str]:
        """发现LLM特定配置文件
        
        Args:
            llm_path: LLM模块路径
            pattern: 文件模式
            
        Returns:
            配置文件路径列表
        """
        config_files = []
        
        # 搜索全局配置文件
        for file_path in llm_path.glob(f"{pattern}.yaml"):
            if file_path.is_file() and file_path.stem.startswith("global"):
                config_files.append(str(file_path))
        
        for file_path in llm_path.glob(f"{pattern}.yml"):
            if file_path.is_file() and file_path.stem.startswith("global"):
                config_files.append(str(file_path))
        
        # 搜索provider目录下的配置文件
        provider_dir = llm_path / "provider"
        if provider_dir.exists():
            for provider_path in provider_dir.iterdir():
                if provider_path.is_dir():
                    # 搜索common配置文件
                    for ext in ['.yaml', '.yml']:
                        common_file = provider_path / f"common{ext}"
                        if common_file.is_file():
                            config_files.append(str(common_file))
                    
                    # 搜索模型特定配置文件
                    for file_path in provider_path.glob(f"{pattern}.yaml"):
                        if file_path.is_file() and file_path.stem != "common":
                            config_files.append(str(file_path))
                    
                    for file_path in provider_path.glob(f"{pattern}.yml"):
                        if file_path.is_file() and file_path.stem != "common":
                            config_files.append(str(file_path))
        
        return config_files
    
    def get_config_info(self, config_path: str) -> Dict[str, Any]:
        """获取配置文件信息
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置文件信息
        """
        try:
            path = Path(config_path)
            
            if not path.exists():
                return {
                    "path": config_path,
                    "exists": False,
                    "error": "文件不存在"
                }
            
            # 基本文件信息
            stat = path.stat()
            info = {
                "path": str(path),
                "name": path.name,
                "stem": path.stem,
                "suffix": path.suffix,
                "exists": True,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_readable": os.access(path, os.R_OK)
            }
            
            # 尝试解析配置内容
            if info["is_readable"] and path.suffix.lower() in ['.yaml', '.yml']:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = yaml.safe_load(f)
                    
                    if content:
                        info["content_type"] = type(content).__name__
                        info["keys"] = list(content.keys()) if isinstance(content, dict) else []
                        info["depth"] = self._calculate_depth(content)
                        
                        # 检查继承关系
                        if isinstance(content, dict) and "_inherit_" in content:
                            info["inheritance"] = content["_inherit_"]
                        
                        # 检查环境变量引用
                        info["env_refs"] = self._find_env_references(content)
                        
                except Exception as e:
                    info["parse_error"] = str(e)
            
            return info
            
        except Exception as e:
            logger.error(f"获取配置信息失败 {config_path}: {e}")
            return {
                "path": config_path,
                "exists": False,
                "error": str(e)
            }
    
    def validate_config_path(self, config_path: str) -> bool:
        """验证配置文件路径是否有效
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            是否有效
        """
        try:
            path = Path(config_path)
            
            # 检查文件是否存在
            if not path.exists():
                return False
            
            # 检查是否为文件
            if not path.is_file():
                return False
            
            # 检查文件扩展名
            if path.suffix.lower() not in ['.yaml', '.yml']:
                return False
            
            # 检查文件是否可读
            if not os.access(path, os.R_OK):
                return False
            
            # 尝试解析文件
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
                return True
            except Exception:
                return False
                
        except Exception as e:
            logger.error(f"验证配置路径失败 {config_path}: {e}")
            return False
    
    def get_config_dependencies(self, config_path: str) -> List[str]:
        """获取配置文件依赖
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            依赖的配置文件路径列表
        """
        try:
            dependencies = []
            path = Path(config_path)
            
            if not path.exists() or not path.is_file():
                return dependencies
            
            # 解析配置文件
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                
                if not isinstance(content, dict):
                    return dependencies
                
                # 检查继承依赖
                if "_inherit_" in content:
                    inherit_config = content["_inherit_"]
                    if isinstance(inherit_config, str):
                        # 相对路径解析
                        inherit_path = path.parent / inherit_config
                        if not inherit_path.suffix:
                            inherit_path = inherit_path.with_suffix('.yaml')
                        dependencies.append(str(inherit_path))
                    elif isinstance(inherit_config, list):
                        for inherit_item in inherit_config:
                            inherit_path = path.parent / inherit_item
                            if not inherit_path.suffix:
                                inherit_path = inherit_path.with_suffix('.yaml')
                            dependencies.append(str(inherit_path))
                
                # 检查引用依赖
                refs = self._find_config_references(content)
                for ref in refs:
                    ref_path = path.parent / ref
                    if not ref_path.suffix:
                        ref_path = ref_path.with_suffix('.yaml')
                    dependencies.append(str(ref_path))
                
            except Exception as e:
                logger.error(f"解析配置依赖失败 {config_path}: {e}")
            
            # 去重并返回
            return list(set(dependencies))
            
        except Exception as e:
            logger.error(f"获取配置依赖失败 {config_path}: {e}")
            return []
    
    def resolve_config_path(self, config_name: str, module_type: Optional[str] = None) -> str:
        """解析配置文件路径
        
        Args:
            config_name: 配置名称
            module_type: 模块类型（可选）
            
        Returns:
            解析后的配置文件路径
        """
        try:
            # 如果已经是完整路径，直接返回
            if Path(config_name).is_absolute():
                return config_name
            
            # 构建路径
            if module_type:
                config_path = self.base_path / module_type / config_name
            else:
                config_path = self.base_path / config_name
            
            # 如果没有扩展名，添加.yaml
            if not config_path.suffix:
                config_path = config_path.with_suffix('.yaml')
            
            return str(config_path)
            
        except Exception as e:
            logger.error(f"解析配置路径失败 {config_name}: {e}")
            return config_name
    
    def watch_config_changes(self, config_path: str, callback: Callable) -> None:
        """监听配置文件变化
        
        Args:
            config_path: 配置文件路径
            callback: 变化回调函数
        """
        # 简单实现：存储回调函数
        # 实际的文件监听需要更复杂的实现（如watchdog库）
        self._watchers[config_path] = callback
        logger.debug(f"注册配置文件监听: {config_path}")
    
    def stop_watching(self, config_path: str) -> None:
        """停止监听配置文件变化
        
        Args:
            config_path: 配置文件路径
        """
        if config_path in self._watchers:
            del self._watchers[config_path]
            logger.debug(f"停止监听配置文件: {config_path}")
    
    def get_last_modified(self, config_path: str) -> Optional[datetime]:
        """获取配置文件最后修改时间
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            最后修改时间，如果文件不存在则返回None
        """
        try:
            path = Path(config_path)
            
            if not path.exists():
                return None
            
            stat = path.stat()
            return datetime.fromtimestamp(stat.st_mtime)
            
        except Exception as e:
            logger.error(f"获取最后修改时间失败 {config_path}: {e}")
            return None
    
    def _calculate_depth(self, obj: Any, current_depth: int = 0) -> int:
        """计算配置内容的深度"""
        if current_depth > 10:  # 防止无限递归
            return current_depth
        
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(self._calculate_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, (list, tuple)):
            if not obj:
                return current_depth
            return max(self._calculate_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth
    
    def _find_env_references(self, obj: Any, path: str = "") -> List[str]:
        """查找环境变量引用"""
        references = []
        
        if isinstance(obj, str):
            # 查找 ${VAR:DEFAULT} 格式的环境变量引用
            import re
            matches = re.findall(r'\$\{([^}]+)\}', obj)
            for match in matches:
                references.append(f"{path}.{match}" if path else match)
        elif isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                references.extend(self._find_env_references(value, current_path))
        elif isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                references.extend(self._find_env_references(item, current_path))
        
        return references
    
    def _find_config_references(self, obj: Any, path: str = "") -> List[str]:
        """查找配置文件引用"""
        references = []
        
        if isinstance(obj, str) and obj.endswith(('.yaml', '.yml')):
            references.append(obj)
        elif isinstance(obj, dict):
            for key, value in obj.items():
                if key not in ['_inherit_']:  # 跳过继承字段，单独处理
                    references.extend(self._find_config_references(value, path))
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                references.extend(self._find_config_references(item, path))
        
        return references