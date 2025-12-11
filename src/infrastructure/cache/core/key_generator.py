"""缓存键生成器

提供通用的缓存键生成功能，支持多种策略：
1. 基于内容的哈希
2. 基于参数的哈希
3. 分层键生成
4. 版本化键生成
5. 特殊场景：提示词引用、节点配置等

支持多种哈希算法：
- SHA256：推荐用于生产环境，安全性高
- MD5：保留用于兼容性，适用于非安全场景
"""

import hashlib
import json
import re
from typing import Any, Dict, Optional, Sequence, Union, Literal, List
from src.interfaces.llm import ICacheKeyGenerator
from src.interfaces.dependency_injection import get_logger

logger = get_logger(__name__)


class BaseKeySerializer:
    """基础键序列化器，提供通用的序列化功能"""
    
    @staticmethod
    def serialize_value(value: Any) -> str:
        """
        序列化值为字符串
        
        Args:
            value: 要序列化的值
            
        Returns:
            序列化后的字符串
        """
        if isinstance(value, str):
            return value
        elif isinstance(value, (int, float, bool)):
            return str(value)
        elif isinstance(value, (list, tuple)):
            return f"[{','.join(BaseKeySerializer.serialize_value(v) for v in value)}]"
        elif isinstance(value, dict):
            items = []
            for k, v in sorted(value.items()):
                items.append(f"{k}:{BaseKeySerializer.serialize_value(v)}")
            return f"{{{','.join(items)}}}"
        elif isinstance(value, Sequence) and not isinstance(value, str):
            return f"[{','.join(BaseKeySerializer.serialize_value(v) for v in value)}]"
        else:
            # 对于复杂对象，使用JSON序列化
            try:
                return json.dumps(value, sort_keys=True, default=str)
            except (TypeError, ValueError):
                return str(value)
    
    @staticmethod
    def hash_string(text: str, algorithm: str = "md5") -> str:
        """
        生成字符串哈希
        
        Args:
            text: 要哈希的文本
            algorithm: 哈希算法，支持 'sha256' 和 'md5'
            
        Returns:
            哈希值
        """
        if algorithm == "sha256":
            return hashlib.sha256(text.encode()).hexdigest()
        else:
            return hashlib.md5(text.encode()).hexdigest()
    
    @staticmethod
    def json_dumps(obj: Any) -> str:
        """JSON序列化"""
        return json.dumps(obj, sort_keys=True)


class DefaultCacheKeyGenerator(ICacheKeyGenerator):
    """默认缓存键生成器
    
    实现 ICacheKeyGenerator 接口，支持多种缓存键生成策略。
    """
    
    # 支持的哈希算法
    SUPPORTED_HASH_ALGORITHMS = Literal["sha256", "md5"]
    
    # 默认哈希算法
    DEFAULT_HASH_ALGORITHM = "sha256"
    
    # 最大递归深度，防止栈溢出
    MAX_RECURSION_DEPTH = 50
    
    def generate_key(self, *args, **kwargs) -> str:
        """
        生成缓存键（基础方法）
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            缓存键
        """
        # 将所有参数序列化为字符串
        key_parts = []
        
        # 处理位置参数
        for arg in args:
            key_parts.append(BaseKeySerializer.serialize_value(arg))
        
        # 处理关键字参数
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{BaseKeySerializer.serialize_value(value)}")
        
        # 生成哈希
        key_string = "|".join(key_parts)
        return BaseKeySerializer.hash_string(key_string)
    
    @staticmethod
    def generate_content_key(
        content: str,
        salt: Optional[str] = None,
        algorithm: SUPPORTED_HASH_ALGORITHMS = DEFAULT_HASH_ALGORITHM
    ) -> str:
        """基于内容生成缓存键
        
        Args:
            content: 内容字符串
            salt: 盐值，用于增加随机性
            algorithm: 哈希算法，支持 'sha256' 和 'md5'
            
        Returns:
            缓存键
            
        Raises:
            ValueError: 当内容为空或算法不支持时
        """
        if not content:
            raise ValueError("内容不能为空")
            
        if algorithm not in ["sha256", "md5"]:
            raise ValueError(f"不支持的哈希算法: {algorithm}")
        
        try:
            # 准备数据
            data = content
            if salt:
                data = f"{content}:{salt}"
            
            # 生成哈希
            if algorithm == "sha256":
                return hashlib.sha256(data.encode('utf-8')).hexdigest()
            else:  # md5
                return hashlib.md5(data.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.error(f"生成内容缓存键失败: {e}")
            # 使用更安全的回退机制：基于内容长度和前缀的简单哈希
            fallback = f"fallback_{len(content)}_{content[:10]}"
            return hashlib.md5(fallback.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_params_key(
        params: Dict[str, Any],
        salt: Optional[str] = None,
        algorithm: SUPPORTED_HASH_ALGORITHMS = DEFAULT_HASH_ALGORITHM
    ) -> str:
        """基于参数生成缓存键
        
        Args:
            params: 参数字典
            salt: 盐值
            algorithm: 哈希算法，支持 'sha256' 和 'md5'
            
        Returns:
            缓存键
            
        Raises:
            ValueError: 当参数为空或算法不支持时
        """
        if not params:
            raise ValueError("参数不能为空")
            
        if algorithm not in ["sha256", "md5"]:
            raise ValueError(f"不支持的哈希算法: {algorithm}")
        
        try:
            # 规范化参数
            normalized_params = DefaultCacheKeyGenerator._normalize_params(params, depth=0)
            
            # 转换为JSON字符串
            params_str = json.dumps(normalized_params, sort_keys=True, ensure_ascii=False)
            
            # 添加盐值
            if salt:
                params_str = f"{params_str}:{salt}"
            
            # 生成哈希
            if algorithm == "sha256":
                return hashlib.sha256(params_str.encode('utf-8')).hexdigest()
            else:  # md5
                return hashlib.md5(params_str.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.error(f"生成参数缓存键失败: {e}")
            # 使用更安全的回退机制
            fallback = f"fallback_params_{len(str(params))}_{sorted(params.keys())[:5]}"
            return hashlib.md5(fallback.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_layered_key(
        prefix: str,
        identifier: str,
        layer: str = "default",
        algorithm: SUPPORTED_HASH_ALGORITHMS = DEFAULT_HASH_ALGORITHM
    ) -> str:
        """生成分层缓存键
        
        Args:
            prefix: 前缀
            identifier: 标识符
            layer: 层级
            algorithm: 哈希算法，支持 'sha256' 和 'md5'
            
        Returns:
            分层缓存键
            
        Raises:
            ValueError: 当前缀或标识符为空时
        """
        if not prefix or not identifier:
            raise ValueError("前缀和标识符不能为空")
            
        if algorithm not in ["sha256", "md5"]:
            raise ValueError(f"不支持的哈希算法: {algorithm}")
        
        try:
            # 构建分层键
            layered_key = f"{layer}:{prefix}:{identifier}"
            
            # 生成哈希
            if algorithm == "sha256":
                return hashlib.sha256(layered_key.encode('utf-8')).hexdigest()
            else:  # md5
                return hashlib.md5(layered_key.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.error(f"生成分层缓存键失败: {e}")
            # 回退到非哈希的分层键
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
    def generate_composite_key(
        components: List[str],
        separator: str = ":",
        algorithm: SUPPORTED_HASH_ALGORITHMS = DEFAULT_HASH_ALGORITHM
    ) -> str:
        """生成组合缓存键
        
        Args:
            components: 组件列表
            separator: 分隔符
            algorithm: 哈希算法，支持 'sha256' 和 'md5'
            
        Returns:
            组合缓存键
            
        Raises:
            ValueError: 当组件列表为空或算法不支持时
        """
        if not components:
            raise ValueError("组件列表不能为空")
            
        if algorithm not in ["sha256", "md5"]:
            raise ValueError(f"不支持的哈希算法: {algorithm}")
        
        try:
            # 过滤空组件
            filtered_components = [comp for comp in components if comp]
            
            if not filtered_components:
                raise ValueError("组件列表不能为空")
            
            # 组合组件
            composite_key = separator.join(filtered_components)
            
            # 生成哈希
            if algorithm == "sha256":
                return hashlib.sha256(composite_key.encode('utf-8')).hexdigest()
            else:  # md5
                return hashlib.md5(composite_key.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.error(f"生成组合缓存键失败: {e}")
            # 回退到非哈希的组合键
            filtered_components = [comp for comp in components if comp]
            return separator.join(filtered_components) if filtered_components else "empty_composite"
    
    @staticmethod
    def generate_reference_key(
        prompt_ref: str,
        variables: Dict[str, Any],
        context: Dict[str, Any],
        algorithm: SUPPORTED_HASH_ALGORITHMS = DEFAULT_HASH_ALGORITHM
    ) -> str:
        """生成提示词引用缓存键
        
        Args:
            prompt_ref: 提示词引用
            variables: 变量字典
            context: 上下文字典
            algorithm: 哈希算法，支持 'sha256' 和 'md5'
            
        Returns:
            引用缓存键
            
        Raises:
            ValueError: 当提示词引用为空时
        """
        if not prompt_ref:
            raise ValueError("提示词引用不能为空")
        
        try:
            # 组合数据
            cache_data = {
                "ref": prompt_ref,
                "vars": sorted(variables.items()) if variables else [],
                "context_hash": DefaultCacheKeyGenerator._generate_context_hash(context, algorithm)
            }
            
            # 生成键
            return DefaultCacheKeyGenerator.generate_params_key(cache_data, algorithm=algorithm)
            
        except Exception as e:
            logger.error(f"生成引用缓存键失败: {e}")
            # 使用更安全的回退机制
            fallback = f"ref_fallback_{prompt_ref}_{len(str(variables))}_{len(context)}"
            return hashlib.md5(fallback.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_node_key(
        node_id: str,
        config: Dict[str, Any],
        state_data: Dict[str, Any],
        algorithm: SUPPORTED_HASH_ALGORITHMS = DEFAULT_HASH_ALGORITHM
    ) -> str:
        """生成节点缓存键
        
        Args:
            node_id: 节点ID
            config: 节点配置
            state_data: 状态数据
            algorithm: 哈希算法，支持 'sha256' 和 'md5'
            
        Returns:
            节点缓存键
            
        Raises:
            ValueError: 当节点ID为空时
        """
        if not node_id:
            raise ValueError("节点ID不能为空")
        
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
            
            return DefaultCacheKeyGenerator.generate_params_key(key_config, algorithm=algorithm)
            
        except Exception as e:
            logger.error(f"生成节点缓存键失败: {e}")
            # 使用更安全的回退机制
            fallback = f"node_fallback_{node_id}_{len(str(config))}_{len(str(state_data))}"
            return hashlib.md5(fallback.encode('utf-8')).hexdigest()
    
    @staticmethod
    def _normalize_params(params: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
        """规范化参数字典
        
        Args:
            params: 原始参数
            depth: 当前递归深度，用于防止栈溢出
            
        Returns:
            规范化后的参数
            
        Raises:
            ValueError: 当递归深度超过限制时
        """
        if depth > DefaultCacheKeyGenerator.MAX_RECURSION_DEPTH:
            raise ValueError(f"递归深度超过限制: {DefaultCacheKeyGenerator.MAX_RECURSION_DEPTH}")
        
        normalized = {}
        
        for key, value in params.items():
            if isinstance(value, dict):
                # 递归规范化字典
                normalized[key] = DefaultCacheKeyGenerator._normalize_params(value, depth + 1)
            elif isinstance(value, (list, tuple)):
                # 规范化列表和元组
                normalized[key] = [
                    DefaultCacheKeyGenerator._normalize_params(item, depth + 1) if isinstance(item, dict) else item
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
    def _generate_context_hash(
        context: Dict[str, Any],
        algorithm: SUPPORTED_HASH_ALGORITHMS = DEFAULT_HASH_ALGORITHM
    ) -> str:
        """生成上下文哈希
        
        Args:
            context: 上下文字典
            algorithm: 哈希算法，支持 'sha256' 和 'md5'
            
        Returns:
            上下文哈希值
            
        Note:
            修复了原版本只使用键名忽略值变化的问题，现在包含键和值的变化
        """
        if not context:
            return "empty_context"
            
        if algorithm not in ["sha256", "md5"]:
            algorithm = "md5"  # 默认回退到md5
        
        try:
            # 规范化上下文，包含键和值的变化
            normalized_context = DefaultCacheKeyGenerator._normalize_params(context, depth=0)
            context_str = json.dumps(normalized_context, sort_keys=True, ensure_ascii=False)
            
            # 生成哈希
            if algorithm == "sha256":
                full_hash = hashlib.sha256(context_str.encode('utf-8')).hexdigest()
            else:  # md5
                full_hash = hashlib.md5(context_str.encode('utf-8')).hexdigest()
            
            # 返回前8位作为简短哈希
            return full_hash[:8]
            
        except Exception as e:
            logger.error(f"生成上下文哈希失败: {e}")
            # 使用键名和数量作为回退
            fallback = f"context_fallback_{len(context)}_{sorted(context.keys())[:3]}"
            return hashlib.md5(fallback.encode('utf-8')).hexdigest()[:8]
    
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
