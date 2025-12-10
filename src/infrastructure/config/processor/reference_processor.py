"""引用处理器

处理配置中的引用（如 $ref: path.to.value）。
"""

from typing import Dict, Any, Optional, Set

from .base_processor import BaseConfigProcessor
import logging

logger = logging.getLogger(__name__)


class ReferenceProcessor(BaseConfigProcessor):
    """引用处理器
    
    处理配置中的引用（如 $ref: path.to.value）。
    """
    
    def __init__(self):
        """初始化引用处理器"""
        super().__init__("reference")
        logger.debug("引用处理器初始化完成")
    
    def _process_internal(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
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