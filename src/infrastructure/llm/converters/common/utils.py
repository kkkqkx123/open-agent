"""通用工具函数

提供跨提供商的通用工具函数和辅助方法。
"""

import json
import hashlib
import time
from typing import Dict, Any, List, Optional, Union, Callable
from src.services.logger import get_logger


class CommonUtils:
    """通用工具类"""
    
    def __init__(self) -> None:
        """初始化通用工具类"""
        self.logger = get_logger(__name__)
    
    @staticmethod
    def deep_merge_dict(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典
        
        Args:
            dict1: 第一个字典
            dict2: 第二个字典
            
        Returns:
            Dict[str, Any]: 合并后的字典
        """
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = CommonUtils.deep_merge_dict(result[key], value)
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def flatten_dict(nested_dict: Dict[str, Any], separator: str = ".", prefix: str = "") -> Dict[str, Any]:
        """扁平化嵌套字典
        
        Args:
            nested_dict: 嵌套字典
            separator: 分隔符
            prefix: 前缀
            
        Returns:
            Dict[str, Any]: 扁平化后的字典
        """
        flattened = {}
        
        for key, value in nested_dict.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key
            
            if isinstance(value, dict):
                flattened.update(CommonUtils.flatten_dict(value, separator, new_key))
            else:
                flattened[new_key] = value
        
        return flattened
    
    @staticmethod
    def safe_json_loads(json_str: str, default: Any = None) -> Any:
        """安全的JSON解析
        
        Args:
            json_str: JSON字符串
            default: 默认值
            
        Returns:
            Any: 解析结果或默认值
        """
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return default
    
    @staticmethod
    def safe_json_dumps(obj: Any, default: str = "{}") -> str:
        """安全的JSON序列化
        
        Args:
            obj: 要序列化的对象
            default: 默认值
            
        Returns:
            str: JSON字符串或默认值
        """
        try:
            return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
        except (TypeError, ValueError):
            return default
    
    @staticmethod
    def generate_hash(content: Union[str, Dict[str, Any]], algorithm: str = "md5") -> str:
        """生成内容哈希
        
        Args:
            content: 要哈希的内容
            algorithm: 哈希算法
            
        Returns:
            str: 哈希值
        """
        if isinstance(content, dict):
            content_str = json.dumps(content, sort_keys=True, ensure_ascii=False)
        else:
            content_str = str(content)
        
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(content_str.encode('utf-8'))
        
        return hash_obj.hexdigest()
    
    @staticmethod
    def format_timestamp(timestamp: Optional[float] = None) -> str:
        """格式化时间戳
        
        Args:
            timestamp: 时间戳，默认为当前时间
            
        Returns:
            str: 格式化的时间字符串
        """
        if timestamp is None:
            timestamp = time.time()
        
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        # 移除或替换不安全的字符
        invalid_chars = '<>:"/\\|?*'
        sanitized = filename
        
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # 移除前后空格和点
        sanitized = sanitized.strip(' .')
        
        # 确保不为空
        if not sanitized:
            sanitized = "unnamed"
        
        return sanitized
    
    @staticmethod
    def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
        """截断字符串
        
        Args:
            text: 原始字符串
            max_length: 最大长度
            suffix: 截断后缀
            
        Returns:
            str: 截断后的字符串
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """从文本中提取数字
        
        Args:
            text: 文本内容
            
        Returns:
            List[float]: 提取的数字列表
        """
        import re
        
        # 匹配整数和小数
        pattern = r'-?\d+\.?\d*'
        matches = re.findall(pattern, text)
        
        numbers = []
        for match in matches:
            try:
                if '.' in match:
                    numbers.append(float(match))
                else:
                    numbers.append(int(match))
            except ValueError:
                continue
        
        return numbers
    
    @staticmethod
    def format_bytes(bytes_count: int) -> str:
        """格式化字节数
        
        Args:
            bytes_count: 字节数
            
        Returns:
            str: 格式化的字符串
        """
        if bytes_count == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        size: float = float(bytes_count)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.1f} {units[unit_index]}"
    
    @staticmethod
    def retry_with_backoff(
        func: Callable,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ) -> Any:
        """带退避的重试机制
        
        Args:
            func: 要重试的函数
            max_attempts: 最大尝试次数
            base_delay: 基础延迟时间
            max_delay: 最大延迟时间
            backoff_factor: 退避因子
            exceptions: 要捕获的异常类型
            
        Returns:
            Any: 函数执行结果
            
        Raises:
            最后一次执行的异常
        """
        last_exception: Optional[Exception] = None
        
        for attempt in range(max_attempts):
            try:
                return func()
            except exceptions as e:
                last_exception = e
                
                if attempt == max_attempts - 1:
                    break
                
                delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                time.sleep(delay)
        
        if last_exception is not None:
            raise last_exception
    
    def cache_result(self, cache_key: str, result: Any, ttl: Optional[int] = None) -> None:
        """缓存结果（简单内存缓存）
        
        Args:
            cache_key: 缓存键
            result: 要缓存的结果
            ttl: 过期时间（秒）
        """
        if not hasattr(self, '_cache'):
            self._cache = {}
        
        self._cache[cache_key] = {
            'result': result,
            'timestamp': time.time(),
            'ttl': ttl
        }
    
    def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """获取缓存结果
        
        Args:
            cache_key: 缓存键
            
        Returns:
            Optional[Any]: 缓存的结果或None
        """
        if not hasattr(self, '_cache'):
            return None
        
        cached_item = self._cache.get(cache_key)
        if not cached_item:
            return None
        
        # 检查是否过期
        if cached_item['ttl'] is not None:
            if time.time() - cached_item['timestamp'] > cached_item['ttl']:
                del self._cache[cache_key]
                return None
        
        return cached_item['result']
    
    def clear_cache(self, pattern: Optional[str] = None) -> None:
        """清理缓存
        
        Args:
            pattern: 缓存键模式，如果为None则清理所有缓存
        """
        if not hasattr(self, '_cache'):
            return
        
        if pattern is None:
            self._cache.clear()
        else:
            import re
            keys_to_remove = [key for key in self._cache.keys() if re.match(pattern, key)]
            for key in keys_to_remove:
                del self._cache[key]
    
    @staticmethod
    def convert_size_to_bytes(size_str: str) -> int:
        """将大小字符串转换为字节数
        
        Args:
            size_str: 大小字符串，如 "10MB", "1.5GB"
            
        Returns:
            int: 字节数
        """
        size_str = size_str.upper().strip()
        
        # 提取数字和单位
        import re
        match = re.match(r'^([\d.]+)\s*([KMGT]?B)$', size_str)
        
        if not match:
            raise ValueError(f"无效的大小格式: {size_str}")
        
        number_str, unit = match.groups()
        number = float(number_str)
        
        # 单位转换
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3,
            'TB': 1024 ** 4
        }
        
        multiplier = multipliers.get(unit)
        if multiplier is None:
            raise ValueError(f"不支持的单位: {unit}")
        
        return int(number * multiplier)
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """标准化文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 标准化后的文本
        """
        import unicodedata
        
        # 转换为NFKC形式
        normalized = unicodedata.normalize('NFKC', text)
        
        # 移除控制字符
        normalized = ''.join(char for char in normalized if not unicodedata.category(char).startswith('C'))
        
        # 标准化空白字符
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def measure_execution_time(self, func: Callable, *args, **kwargs) -> tuple[Any, float]:
        """测量函数执行时间
        
        Args:
            func: 要测量的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            tuple[Any, float]: (函数结果, 执行时间秒数)
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        self.logger.debug(f"函数 {func.__name__} 执行时间: {execution_time:.3f}秒")
        
        return result, execution_time
    
    @staticmethod
    def create_request_id() -> str:
        """创建请求ID
        
        Returns:
            str: 唯一的请求ID
        """
        import uuid
        return str(uuid.uuid4())
    
    @staticmethod
    def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
        """遮蔽敏感数据
        
        Args:
            data: 敏感数据
            mask_char: 遮蔽字符
            visible_chars: 可见字符数
            
        Returns:
            str: 遮蔽后的数据
        """
        if len(data) <= visible_chars:
            return mask_char * len(data)
        
        visible_part = data[:visible_chars]
        masked_part = mask_char * (len(data) - visible_chars)
        
        return visible_part + masked_part