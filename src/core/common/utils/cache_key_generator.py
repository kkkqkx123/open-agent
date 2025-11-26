"""缓存键生成器工具类

提供生成缓存键的工具方法。
"""

import hashlib
import json
from typing import Dict, Any, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class CacheKeyGenerator:
    """缓存键生成器工具类
    
    提供各种缓存键生成策略：
    1. 基于内容的哈希
    2. 基于参数的哈希
    3. 分层键生成
    4. 版本化键生成
    """
    
    @staticmethod
    def generate_content_key(content: str, salt: Optional[str] = None) -> str:
        """基于内容生成缓存键
        
        Args:
            content: 内容字符串
            salt: 盐值，用于增加随机性
            
        Returns:
            缓存键
        """
        try:
            # 准备数据
            data = content
            if salt:
                data = f"{content}:{salt}"
            
            # 生成哈希
            return hashlib.md5(data.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.warning(f"生成内容缓存键失败: {e}")
            return str(hash(content))
    
    @staticmethod
    def generate_params_key(params: Dict[str, Any], salt: Optional[str] = None) -> str:
        """基于参数生成缓存键
        
        Args:
            params: 参数字典
            salt: 盐值
            
        Returns:
            缓存键
        """
        try:
            # 规范化参数
            normalized_params = CacheKeyGenerator._normalize_params(params)
            
            # 转换为JSON字符串
            params_str = json.dumps(normalized_params, sort_keys=True, ensure_ascii=False)
            
            # 添加盐值
            if salt:
                params_str = f"{params_str}:{salt}"
            
            # 生成哈希
            return hashlib.md5(params_str.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.warning(f"生成参数缓存键失败: {e}")
            return str(hash(str(params)))
    
    @staticmethod
    def generate_layered_key(prefix: str, identifier: str, layer: str = "default") -> str:
        """生成分层缓存键
        
        Args:
            prefix: 前缀
            identifier: 标识符
            layer: 层级
            
        Returns:
            分层缓存键
        """
        try:
            # 构建分层键
            layered_key = f"{layer}:{prefix}:{identifier}"
            
            # 生成哈希
            return hashlib.md5(layered_key.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.warning(f"生成分层缓存键失败: {e}")
            return f"{layer}:{prefix}:{identifier}"
    
    @staticmethod
    def generate_versioned_key(base_key: str, version: Union[str, int]) -> str:
        """生成版本化缓存键
        
        Args:
            base_key: 基础键
            version: 版本号
            
        Returns:
            版本化缓存键
        """
        try:
            return f"{base_key}:v{version}"
        except Exception as e:
            logger.warning(f"生成版本化缓存键失败: {e}")
            return base_key
    
    @staticmethod
    def generate_composite_key(components: List[str], separator: str = ":") -> str:
        """生成组合缓存键
        
        Args:
            components: 组件列表
            separator: 分隔符
            
        Returns:
            组合缓存键
        """
        try:
            # 过滤空组件
            filtered_components = [comp for comp in components if comp]
            
            if not filtered_components:
                raise ValueError("组件列表不能为空")
            
            # 组合组件
            composite_key = separator.join(filtered_components)
            
            # 生成哈希
            return hashlib.md5(composite_key.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.warning(f"生成组合缓存键失败: {e}")
            return separator.join(components)
    
    @staticmethod
    def generate_reference_key(prompt_ref: str, variables: Dict[str, Any], context: Dict[str, Any]) -> str:
        """生成提示词引用缓存键
        
        Args:
            prompt_ref: 提示词引用
            variables: 变量字典
            context: 上下文字典
            
        Returns:
            引用缓存键
        """
        try:
            # 组合数据
            cache_data = {
                "ref": prompt_ref,
                "vars": sorted(variables.items()) if variables else [],
                "context_hash": CacheKeyGenerator._generate_context_hash(context)
            }
            
            # 生成键
            return CacheKeyGenerator.generate_params_key(cache_data)
            
        except Exception as e:
            logger.warning(f"生成引用缓存键失败: {e}")
            return f"ref:{prompt_ref}"
    
    @staticmethod
    def generate_node_key(node_id: str, config: Dict[str, Any], state_data: Dict[str, Any]) -> str:
        """生成节点缓存键
        
        Args:
            node_id: 节点ID
            config: 节点配置
            state_data: 状态数据
            
        Returns:
            节点缓存键
        """
        try:
            # 提取影响缓存的关键配置
            key_config = {
                "node_id": node_id,
                "system_prompt": config.get("system_prompt"),
                "system_prompt_ref": config.get("system_prompt_ref"),
                "system_prompt_template": config.get("system_prompt_template"),
                "system_prompt_parts": config.get("system_prompt_parts"),
                "user_prompt_id": config.get("user_prompt_id"),
                "user_input": config.get("user_input"),
                "prompt_variables": config.get("prompt_variables", {}),
                "prompt_ids": config.get("prompt_ids", [])
            }
            
            # 添加状态数据的关键字段
            state_keys = ["messages", "data", "context"]
            for key in state_keys:
                if key in state_data:
                    key_config[f"state_{key}"] = state_data[key]
            
            return CacheKeyGenerator.generate_params_key(key_config)
            
        except Exception as e:
            logger.warning(f"生成节点缓存键失败: {e}")
            return f"node:{node_id}"
    
    @staticmethod
    def _normalize_params(params: Dict[str, Any]) -> Dict[str, Any]:
        """规范化参数字典
        
        Args:
            params: 原始参数
            
        Returns:
            规范化后的参数
        """
        normalized = {}
        
        for key, value in params.items():
            if isinstance(value, dict):
                # 递归规范化字典
                normalized[key] = CacheKeyGenerator._normalize_params(value)
            elif isinstance(value, (list, tuple)):
                # 规范化列表和元组
                normalized[key] = [
                    CacheKeyGenerator._normalize_params(item) if isinstance(item, dict) else item
                    for item in value
                ]
            elif isinstance(value, (set, frozenset)):
                # 转换集合为排序后的列表
                normalized[key] = sorted(list(value))
            else:
                # 其他类型直接使用
                normalized[key] = value
        
        return normalized
    
    @staticmethod
    def _generate_context_hash(context: Dict[str, Any]) -> str:
        """生成上下文哈希
        
        Args:
            context: 上下文字典
            
        Returns:
            上下文哈希值
        """
        try:
            # 只使用上下文的键，忽略值的变化
            context_keys = sorted(context.keys())
            context_str = json.dumps(context_keys, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(context_str.encode('utf-8')).hexdigest()[:8]
        except Exception as e:
            logger.warning(f"生成上下文哈希失败: {e}")
            return "context_hash_error"
    
    @staticmethod
    def validate_cache_key(key: str) -> List[str]:
        """验证缓存键
        
        Args:
            key: 缓存键
            
        Returns:
            验证错误列表
        """
        errors = []
        
        if not key:
            errors.append("缓存键不能为空")
            return errors
        
        if len(key) > 255:
            errors.append("缓存键长度不能超过255个字符")
        
        # 检查是否包含非法字符
        import re
        if re.search(r'[<>:"/\\|?*]', key):
            errors.append("缓存键包含非法字符")
        
        return errors
    
    @staticmethod
    def parse_cache_key(key: str) -> Dict[str, Any]:
        """解析缓存键
        
        Args:
            key: 缓存键
            
        Returns:
            解析结果
        """
        try:
            result = {
                "original_key": key,
                "components": [],
                "version": None,
                "layer": None
            }
            
            # 解析版本
            if ":v" in key:
                key_part, version_part = key.rsplit(":v", 1)
                result["original_key"] = key_part
                try:
                    result["version"] = int(version_part)
                except ValueError:
                    result["version"] = version_part
            
            # 解析层级
            if ":" in result["original_key"]:
                parts = result["original_key"].split(":", 1)
                result["layer"] = parts[0]
                result["components"] = parts[1].split(":")
            else:
                result["components"] = [result["original_key"]]
            
            return result
            
        except Exception as e:
            logger.warning(f"解析缓存键失败: {e}")
            return {
                "original_key": key,
                "components": [key],
                "version": None,
                "layer": None,
                "error": str(e)
            }
    
    @staticmethod
    def generate_key_stats(keys: List[str]) -> Dict[str, Any]:
        """生成缓存键统计信息
        
        Args:
            keys: 缓存键列表
            
        Returns:
            统计信息
        """
        try:
            if not keys:
                return {
                    "total_keys": 0,
                    "unique_prefixes": 0,
                    "average_length": 0,
                    "versioned_keys": 0,
                    "layered_keys": 0
                }
            
            total_keys = len(keys)
            total_length = sum(len(key) for key in keys)
            average_length = total_length / total_keys
            
            # 统计前缀
            prefixes = set()
            versioned_keys = 0
            layered_keys = 0
            
            for key in keys:
                # 统计版本化键
                if ":v" in key:
                    versioned_keys += 1
                
                # 统计分层键
                if ":" in key and not key.startswith(":"):
                    layered_keys += 1
                    prefix = key.split(":")[0]
                    prefixes.add(prefix)
            
            return {
                "total_keys": total_keys,
                "unique_prefixes": len(prefixes),
                "average_length": average_length,
                "versioned_keys": versioned_keys,
                "layered_keys": layered_keys,
                "prefixes": list(prefixes)
            }
            
        except Exception as e:
            logger.warning(f"生成缓存键统计失败: {e}")
            return {"error": str(e)}