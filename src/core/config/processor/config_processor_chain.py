"""配置处理器链实现

提供可组合的配置处理功能，支持继承、环境变量替换和引用解析。
"""

from src.services.logger.injection import get_logger
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

from ....interfaces.config.interfaces import IConfigProcessor

logger = get_logger(__name__)


class ConfigProcessorChain(IConfigProcessor):
    """配置处理器链
    
    按顺序执行多个配置处理器，支持配置的逐步处理。
    """
    
    def __init__(self):
        """初始化配置处理器链"""
        self.processors: List[IConfigProcessor] = []
        logger.debug("配置处理器链初始化完成")
    
    def add_processor(self, processor: IConfigProcessor) -> None:
        """添加处理器
        
        Args:
            processor: 配置处理器
        """
        self.processors.append(processor)
        logger.debug(f"已添加配置处理器: {processor.__class__.__name__}")
    
    def remove_processor(self, processor: IConfigProcessor) -> bool:
        """移除处理器
        
        Args:
            processor: 配置处理器
            
        Returns:
            是否成功移除
        """
        if processor in self.processors:
            self.processors.remove(processor)
            logger.debug(f"已移除配置处理器: {processor.__class__.__name__}")
            return True
        return False
    
    def clear_processors(self) -> None:
        """清除所有处理器"""
        self.processors.clear()
        logger.debug("已清除所有配置处理器")
    
    def process(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """按顺序处理配置
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        result = config
        
        for i, processor in enumerate(self.processors):
            try:
                logger.debug(f"执行处理器 {i+1}/{len(self.processors)}: {processor.__class__.__name__}")
                result = processor.process(result, config_path)
            except Exception as e:
                logger.error(f"处理器 {processor.__class__.__name__} 执行失败: {e}")
                raise
        
        logger.debug(f"配置处理完成，共执行 {len(self.processors)} 个处理器")
        return result
    
    def get_processor_count(self) -> int:
        """获取处理器数量
        
        Returns:
            处理器数量
        """
        return len(self.processors)
    
    def get_processor_names(self) -> List[str]:
        """获取处理器名称列表
        
        Returns:
            处理器名称列表
        """
        return [processor.__class__.__name__ for processor in self.processors]


class InheritanceProcessor(IConfigProcessor):
    """继承处理器
    
    处理配置文件之间的继承关系。
    """
    
    def __init__(self):
        """初始化继承处理器"""
        self._loading_stack: List[str] = []
        logger.debug("继承处理器初始化完成")
    
    def process(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """处理配置继承
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        # 检查循环继承
        if config_path in self._loading_stack:
            cycle_path = " -> ".join(self._loading_stack[self._loading_stack.index(config_path):] + [config_path])
            raise ValueError(f"检测到循环继承: {cycle_path}")
        
        # 检查是否有继承配置
        inherits_from = config.get("inherits_from")
        if not inherits_from:
            return config
        
        self._loading_stack.append(config_path)
        
        try:
            # 加载父配置
            parent_config = self._load_parent_config(inherits_from, config_path)
            
            # 合并配置（子配置覆盖父配置）
            merged_config = self._merge_configs(parent_config, config)
            
            # 递归处理继承链，但只在父配置有继承时才继续
            if "inherits_from" in merged_config:
                result = self.process(merged_config, config_path)
            else:
                result = merged_config
            
            return result
            
        finally:
            self._loading_stack.pop()
    
    def _load_parent_config(self, inherits_from: str, current_path: str) -> Dict[str, Any]:
        """加载父配置
        
        Args:
            inherits_from: 继承的配置路径
            current_path: 当前配置路径
            
        Returns:
            父配置数据
        """
        # 解析继承路径
        if isinstance(inherits_from, list):
            # 多重继承，合并多个父配置
            parent_config = {}
            for parent_path in inherits_from:
                single_parent = self._load_single_parent_config(parent_path, current_path)
                parent_config = self._merge_configs(parent_config, single_parent)
            return parent_config
        else:
            # 单一继承
            return self._load_single_parent_config(inherits_from, current_path)
    
    def _load_single_parent_config(self, parent_path: str, current_path: str) -> Dict[str, Any]:
        """加载单个父配置
        
        Args:
            parent_path: 父配置路径
            current_path: 当前配置路径
            
        Returns:
            父配置数据
        """
        # 构建完整的父配置路径
        current_dir = Path(current_path).parent
        full_parent_path = current_dir / parent_path
        
        if not full_parent_path.suffix:
            full_parent_path = full_parent_path.with_suffix('.yaml')
        
        if not full_parent_path.exists():
            raise FileNotFoundError(f"继承配置文件不存在: {full_parent_path}")
        
        # 加载父配置文件
        import yaml
        with open(full_parent_path, 'r', encoding='utf-8') as f:
            parent_config = yaml.safe_load(f) or {}
        
        return parent_config
    
    def _merge_configs(self, parent: Dict[str, Any], child: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置（子配置覆盖父配置）
        
        Args:
            parent: 父配置
            child: 子配置
            
        Returns:
            合并后的配置
        """
        result = parent.copy()
        
        for key, value in child.items():
            if key == "inherits_from":
                # 跳过inherits_from字段，因为它已在上层处理
                continue
            
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # 如果两个值都是字典，递归合并
                result[key] = self._merge_configs(result[key], value)
            else:
                # 否则直接覆盖
                result[key] = value
        
        return result


class EnvironmentVariableProcessor(IConfigProcessor):
    """环境变量处理器
    
    处理配置中的环境变量替换。
    """
    
    def __init__(self):
        """初始化环境变量处理器"""
        import re
        self._env_var_pattern = re.compile(r"\$\{([^}]+)\}")
        logger.debug("环境变量处理器初始化完成")
    
    def process(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """处理环境变量替换
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        return self._resolve_env_vars_recursive(config)
    
    def _resolve_env_vars_recursive(self, obj: Any) -> Any:
        """递归解析环境变量
        
        Args:
            obj: 要处理的对象
            
        Returns:
            处理后的对象
        """
        if isinstance(obj, dict):
            return {k: self._resolve_env_vars_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_env_vars_recursive(item) for item in obj]
        elif isinstance(obj, str):
            return self._resolve_env_var_string(obj)
        else:
            return obj
    
    def _resolve_env_var_string(self, text: str) -> str:
        """解析字符串中的环境变量
        
        Args:
            text: 包含环境变量的字符串
            
        Returns:
            解析后的字符串
        """
        import os
        
        def replace_env_var(match):
            var_expr = match.group(1)
            
            # 检查是否包含默认值
            if ":" in var_expr:
                var_name, default_value = var_expr.split(":", 1)
                return os.getenv(var_name.strip(), default_value.strip())
            else:
                # 普通环境变量
                var_name = var_expr.strip()
                value = os.getenv(var_name)
                if value is None:
                    logger.warning(f"环境变量未定义: {var_name}")
                    return f"${{{var_name}}}"
                return value
        
        # 使用正则表达式替换所有环境变量
        return self._env_var_pattern.sub(replace_env_var, text)


class ReferenceProcessor(IConfigProcessor):
    """引用处理器
    
    处理配置中的引用（如 $ref: path.to.value）。
    """
    
    def __init__(self):
        """初始化引用处理器"""
        logger.debug("引用处理器初始化完成")
    
    def process(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """处理配置引用
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        return self._resolve_references_recursive(config, config)
    
    def _resolve_references_recursive(self, obj: Any, root: Dict[str, Any], path: str = "", visited: Optional[set] = None) -> Any:
        """递归解析引用
        
        Args:
            obj: 要处理的对象
            root: 根配置对象
            path: 当前路径
            visited: 已访问的路径集合（用于检测循环引用）
            
        Returns:
            处理后的对象
        """
        if visited is None:
            visited = set()
        
        if isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                current_path = f"{path}.{k}" if path else k
                if isinstance(v, str) and v.startswith("$ref:"):
                    # 解析引用
                    ref_path = v[5:].strip()  # 移除 "$ref:"
                    
                    # 检测循环引用
                    if ref_path in visited:
                        raise ValueError(f"检测到循环引用: {' -> '.join(visited)} -> {ref_path}")
                    
                    # 添加到已访问集合
                    new_visited = visited.copy()
                    new_visited.add(ref_path)
                    
                    ref_value = self._get_nested_value(root, ref_path)
                    result[k] = self._resolve_references_recursive(ref_value, root, current_path, new_visited)
                else:
                    result[k] = self._resolve_references_recursive(v, root, current_path, visited)
            return result
        elif isinstance(obj, list):
            return [self._resolve_references_recursive(item, root, path, visited) for item in obj]
        else:
            return obj
    
    def _get_nested_value(self, obj: Dict[str, Any], path: str) -> Any:
        """获取嵌套字典中的值
        
        Args:
            obj: 字典对象
            path: 路径（点分隔）
            
        Returns:
            对应的值
        """
        keys = path.split(".")
        current = obj
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                raise ValueError(f"引用路径不存在: {path}")
        
        return current