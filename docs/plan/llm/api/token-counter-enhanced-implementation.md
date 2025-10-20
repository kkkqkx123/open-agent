# Token计数器增强实现代码

## 概述

本文档提供了基于API返回体token信息的增强型token计数器的具体实现代码。这些实现可以直接集成到现有的 [`src/llm/token_counter.py`](src/llm/token_counter.py) 文件中。

## 核心组件实现

### 1. API响应解析器

```python
import re
import time
import statistics
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING, Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class TokenUsage:
    """Token使用数据结构"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    source: str = "local"  # "local" 或 "api"
    timestamp: datetime = None
    additional_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.additional_info is None:
            self.additional_info = {}

class ApiResponseParser:
    """API响应解析器，提取token使用信息"""
    
    @staticmethod
    def parse_openai_response(response: Dict[str, Any]) -> TokenUsage:
        """解析OpenAI API响应"""
        usage = response.get("usage", {})
        return TokenUsage(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            source="api",
            additional_info={
                "model": response.get("model"),
                "response_id": response.get("id")
            }
        )
    
    @staticmethod
    def parse_gemini_response(response: Dict[str, Any]) -> TokenUsage:
        """解析Gemini API响应"""
        metadata = response.get("usageMetadata", {})
        return TokenUsage(
            prompt_tokens=metadata.get("promptTokenCount", 0),
            completion_tokens=metadata.get("candidatesTokenCount", 0),
            total_tokens=metadata.get("totalTokenCount", 0),
            source="api",
            additional_info={
                "thoughts_tokens": metadata.get("thoughtsTokenCount", 0),
                "cached_tokens": metadata.get("cachedContentTokenCount", 0),
                "model": response.get("model")
            }
        )
    
    @staticmethod
    def parse_anthropic_response(response: Dict[str, Any]) -> TokenUsage:
        """解析Anthropic API响应"""
        usage = response.get("usage", {})
        return TokenUsage(
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            source="api",
            additional_info={
                "cache_creation_tokens": usage.get("cache_creation_input_tokens", 0),
                "cache_read_tokens": usage.get("cache_read_input_tokens", 0),
                "model": response.get("model")
            }
        )
    
    @staticmethod
    def parse_response(provider: str, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """通用响应解析器"""
        try:
            if provider == "openai":
                return ApiResponseParser.parse_openai_response(response)
            elif provider == "gemini":
                return ApiResponseParser.parse_gemini_response(response)
            elif provider == "anthropic":
                return ApiResponseParser.parse_anthropic_response(response)
            else:
                logger.warning(f"Unknown provider: {provider}")
                return None
        except Exception as e:
            logger.error(f"Failed to parse {provider} response: {e}")
            return None
```

### 2. Token使用缓存管理器

```python
class TokenUsageCache:
    """Token使用缓存管理器"""
    
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        self.cache: Dict[str, TokenUsage] = {}
        self.timestamps: Dict[str, float] = {}
        self.access_times: Dict[str, float] = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def set(self, key: str, usage: TokenUsage):
        """设置缓存"""
        # 检查缓存大小限制
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        self.cache[key] = usage
        self.timestamps[key] = time.time()
        self.access_times[key] = time.time()
    
    def get(self, key: str) -> Optional[TokenUsage]:
        """获取缓存"""
        if key in self.cache:
            current_time = time.time()
            
            # 检查TTL
            if current_time - self.timestamps[key] < self.ttl:
                self.access_times[key] = current_time
                self._hits += 1
                return self.cache[key]
            else:
                # 过期清理
                del self.cache[key]
                del self.timestamps[key]
                del self.access_times[key]
        
        self._misses += 1
        return None
    
    def _evict_lru(self):
        """LRU淘汰策略"""
        if not self.access_times:
            return
        
        # 找到最久未访问的key
        lru_key = min(self.access_times.keys(), 
                     key=lambda k: self.access_times[k])
        
        del self.cache[lru_key]
        del self.timestamps[lru_key]
        del self.access_times[lru_key]
        self._evictions += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "evictions": self._evictions,
            "avg_age": self._calculate_avg_age()
        }
    
    def _calculate_avg_age(self) -> float:
        """计算平均缓存年龄"""
        if not self.timestamps:
            return 0.0
        
        current_time = time.time()
        ages = [current_time - ts for ts in self.timestamps.values()]
        return statistics.mean(ages)
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.timestamps.clear()
        self.access_times.clear()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
```

### 3. Token校准器

```python
class TokenCalibrator:
    """Token计数校准器"""
    
    def __init__(self, min_data_points: int = 3, max_data_points: int = 100):
        self.calibration_data: List[Tuple[int, int]] = []  # (local, api)
        self.calibration_factor = 1.0
        self.min_data_points = min_data_points
        self.max_data_points = max_data_points
        self._last_update = None
    
    def add_calibration_point(self, local_count: int, api_count: int):
        """添加校准数据点"""
        if local_count <= 0 or api_count <= 0:
            logger.warning("Invalid calibration data: non-positive counts")
            return
        
        self.calibration_data.append((local_count, api_count))
        
        # 限制数据点数量
        if len(self.calibration_data) > self.max_data_points:
            self.calibration_data.pop(0)
        
        self._recalculate_factor()
        self._last_update = datetime.now()
    
    def _recalculate_factor(self):
        """重新计算校准因子"""
        if len(self.calibration_data) < self.min_data_points:
            return
        
        # 使用中位数比率，避免异常值影响
        ratios = [api / local for local, api in self.calibration_data]
        
        # 过滤掉极端值（超过2倍或小于0.5倍）
        filtered_ratios = [r for r in ratios if 0.5 <= r <= 2.0]
        
        if filtered_ratios:
            self.calibration_factor = statistics.median(filtered_ratios)
        else:
            # 如果过滤后没有数据，使用原始数据的中位数
            self.calibration_factor = statistics.median(ratios)
    
    def calibrate(self, local_count: int) -> int:
        """校准本地计数"""
        if len(self.calibration_data) < self.min_data_points:
            return local_count
        
        return int(local_count * self.calibration_factor)
    
    def get_confidence(self) -> float:
        """获取校准置信度"""
        if len(self.calibration_data) < self.min_data_points:
            return 0.0
        
        # 基于数据点数量和方差计算置信度
        ratios = [api / local for local, api in self.calibration_data]
        variance = statistics.variance(ratios) if len(ratios) > 1 else 0
        
        # 基础置信度（数据点越多越高）
        base_confidence = min(len(self.calibration_data) / 20, 1.0)
        
        # 方差惩罚（方差越大，置信度越低）
        variance_penalty = min(variance / 0.2, 1.0)
        
        confidence = max(0.0, base_confidence - variance_penalty * 0.5)
        
        # 确保至少有最小置信度
        return max(confidence, 0.1)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取校准统计"""
        if not self.calibration_data:
            return {"data_points": 0, "confidence": 0.0}
        
        ratios = [api / local for local, api in self.calibration_data]
        return {
            "data_points": len(self.calibration_data),
            "calibration_factor": self.calibration_factor,
            "confidence": self.get_confidence(),
            "ratio_mean": statistics.mean(ratios),
            "ratio_std": statistics.stdev(ratios) if len(ratios) > 1 else 0,
            "last_update": self._last_update
        }
```

### 4. 增强的基础计数器

```python
class EnhancedTokenCounter(ITokenCounter):
    """增强的Token计数器基类"""
    
    def __init__(self, model_name: str, provider: str):
        self.model_name = model_name
        self.provider = provider
        self.cache = TokenUsageCache()
        self.calibrator = TokenCalibrator()
        self._api_usage_stats = {
            "total_requests": 0,
            "api_hits": 0,
            "calibration_uses": 0
        }
    
    @abstractmethod
    def _local_count_tokens(self, text: str) -> int:
        """本地token计数（由子类实现）"""
        pass
    
    @abstractmethod
    def _local_count_messages_tokens(self, messages: List[BaseMessage]) -> int:
        """本地消息token计数（由子类实现）"""
        pass
    
    def update_from_api_response(self, response: Dict[str, Any], 
                                 context: Optional[str] = None) -> bool:
        """从API响应更新token信息"""
        try:
            usage = ApiResponseParser.parse_response(self.provider, response)
            if not usage:
                return False
            
            # 生成缓存key
            cache_key = self._generate_cache_key(context or str(response))
            
            # 更新缓存
            self.cache.set(cache_key, usage)
            
            # 更新校准器（如果有本地计数）
            if context:
                local_count = self._local_count_tokens(context)
                self.calibrator.add_calibration_point(local_count, usage.total_tokens)
            
            self._api_usage_stats["api_hits"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to update from {self.provider} API response: {e}")
            return False
    
    def count_tokens(self, text: str) -> int:
        """增强的token计数"""
        self._api_usage_stats["total_requests"] += 1
        
        # 生成缓存key
        cache_key = self._generate_cache_key(text)
        
        # 检查缓存
        cached_usage = self.cache.get(cache_key)
        if cached_usage:
            return cached_usage.total_tokens
        
        # 使用本地计数
        local_count = self._local_count_tokens(text)
        
        # 应用校准（如果置信度足够）
        if self.calibrator.get_confidence() > 0.5:
            calibrated_count = self.calibrator.calibrate(local_count)
            self._api_usage_stats["calibration_uses"] += 1
            return calibrated_count
        
        return local_count
    
    def count_messages_tokens(self, messages: List[BaseMessage]) -> int:
        """增强的消息token计数"""
        # 将消息转换为文本进行缓存
        text_context = self._messages_to_text(messages)
        
        # 使用增强的计数逻辑
        return self.count_tokens(text_context)
    
    def _generate_cache_key(self, content: str) -> str:
        """生成缓存key"""
        # 使用内容的哈希值作为key
        import hashlib
        return hashlib.md5(f"{self.provider}:{self.model_name}:{content}".encode()).hexdigest()
    
    def _messages_to_text(self, messages: List[BaseMessage]) -> str:
        """将消息列表转换为文本"""
        texts = []
        for message in messages:
            content = _extract_content_as_string(message.content)
            texts.append(f"{message.role}:{content}")
        return "\n".join(texts)
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        base_info = {
            "model_name": self.model_name,
            "provider": self.provider,
            "supports_api_usage": True,
            "calibration_confidence": self.calibrator.get_confidence(),
            "cache_stats": self.cache.get_stats(),
            "api_usage_stats": self._api_usage_stats
        }
        
        # 添加校准统计
        if self.calibrator.get_confidence() > 0:
            base_info["calibration_stats"] = self.calibrator.get_stats()
        
        return base_info
    
    def get_last_api_usage(self) -> Optional[TokenUsage]:
        """获取最近的API使用情况"""
        # 从缓存中获取最近的使用情况
        if self.cache.cache:
            latest_key = max(self.cache.timestamps.keys(), 
                           key=lambda k: self.cache.timestamps[k])
            return self.cache.cache.get(latest_key)
        return None
    
    def is_api_usage_available(self) -> bool:
        """检查是否有可用的API使用数据"""
        return self.calibrator.get_confidence() > 0.3
```

### 5. 具体的增强计数器实现

```python
class EnhancedOpenAITokenCounter(EnhancedTokenCounter):
    """增强的OpenAI Token计数器"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        super().__init__(model_name, "openai")
        self._encoding: Optional[EncodingProtocol] = None
        self._load_encoding()
    
    def _load_encoding(self) -> None:
        """加载编码器"""
        try:
            import tiktoken
            
            # 尝试获取模型特定的编码器
            try:
                self._encoding = tiktoken.encoding_for_model(self.model_name)
            except KeyError:
                # 如果模型没有特定编码器，使用默认的
                self._encoding = tiktoken.get_encoding("cl100k_base")
                
        except ImportError:
            self._encoding = None
            logger.warning("tiktoken not available, falling back to estimation")
    
    def _local_count_tokens(self, text: str) -> int:
        """本地token计数"""
        if self._encoding:
            return len(self._encoding.encode(text))
        else:
            # 简单估算：大约4个字符=1个token
            return len(text) // 4
    
    def _local_count_messages_tokens(self, messages: List[BaseMessage]) -> int:
        """本地消息token计数"""
        if self._encoding:
            total_tokens = 0
            
            # 每条消息的开销
            tokens_per_message = 3
            tokens_per_name = 1
            
            for message in messages:
                # 计算消息内容的token
                total_tokens += tokens_per_message
                total_tokens += len(
                    self._encoding.encode(_extract_content_as_string(message.content))
                )
                
                # 如果有名称，添加名称的token
                if hasattr(message, "name") and message.name:
                    total_tokens += tokens_per_name + len(
                        self._encoding.encode(message.name)
                    )
            
            # 添加回复的token
            total_tokens += 3
            
            return total_tokens
        else:
            # 简单估算
            total_chars = sum(len(str(message.content)) for message in messages)
            return total_chars // 4

class EnhancedGeminiTokenCounter(EnhancedTokenCounter):
    """增强的Gemini Token计数器"""
    
    def __init__(self, model_name: str = "gemini-pro"):
        super().__init__(model_name, "gemini")
    
    def _local_count_tokens(self, text: str) -> int:
        """本地token计数"""
        # Gemini使用简单的字符估算
        return len(text) // 4
    
    def _local_count_messages_tokens(self, messages: List[BaseMessage]) -> int:
        """本地消息token计数"""
        total_tokens = 0
        
        for message in messages:
            # 每条消息内容的token
            content_tokens = self._local_count_tokens(
                _extract_content_as_string(message.content)
            )
            total_tokens += content_tokens
            
            # 添加格式化的token（每个消息4个token）
            total_tokens += 4
        
        # 添加回复的token（3个token）
        total_tokens += 3
        
        return total_tokens

class EnhancedAnthropicTokenCounter(EnhancedTokenCounter):
    """增强的Anthropic Token计数器"""
    
    def __init__(self, model_name: str = "claude-3-sonnet-20240229"):
        super().__init__(model_name, "anthropic")
    
    def _local_count_tokens(self, text: str) -> int:
        """本地token计数"""
        # Anthropic使用Claude的token计算方式
        return len(text) // 4
    
    def _local_count_messages_tokens(self, messages: List[BaseMessage]) -> int:
        """本地消息token计数"""
        total_tokens = 0
        
        for message in messages:
            # 每条消息内容的token
            content_tokens = self._local_count_tokens(
                _extract_content_as_string(message.content)
            )
            total_tokens += content_tokens
            
            # 添加格式化的token（每个消息4个token）
            total_tokens += 4
        
        # 添加回复的token（3个token）
        total_tokens += 3
        
        return total_tokens
```

### 6. 增强的工厂类

```python
class EnhancedTokenCounterFactory:
    """增强的Token计数器工厂"""
    
    @staticmethod
    def create_counter(model_type: str, model_name: str) -> EnhancedTokenCounter:
        """创建增强的Token计数器"""
        if model_type == "openai":
            return EnhancedOpenAITokenCounter(model_name)
        elif model_type == "gemini":
            return EnhancedGeminiTokenCounter(model_name)
        elif model_type in ["anthropic", "claude"]:
            return EnhancedAnthropicTokenCounter(model_name)
        else:
            # 默认使用增强的OpenAI计数器
            return EnhancedOpenAITokenCounter(model_name)
    
    @staticmethod
    def get_supported_types() -> List[str]:
        """获取支持的模型类型"""
        return ["openai", "gemini", "anthropic", "claude"]
    
    @staticmethod
    def create_with_config(config: Dict[str, Any]) -> EnhancedTokenCounter:
        """根据配置创建计数器"""
        model_type = config.get("model_type", "openai")
        model_name = config.get("model_name", "gpt-3.5-turbo")
        
        counter = EnhancedTokenCounterFactory.create_counter(model_type, model_name)
        
        # 应用额外配置
        if "cache_ttl" in config:
            counter.cache.ttl = config["cache_ttl"]
        
        if "cache_size" in config:
            counter.cache.max_size = config["cache_size"]
        
        return counter
```

## 使用示例

### 基本使用

```python
# 创建增强的计数器
counter = EnhancedTokenCounterFactory.create_counter("openai", "gpt-4")

# 本地计数
token_count = counter.count_tokens("Hello, world!")

# 模拟API响应更新
api_response = {
    "usage": {
        "prompt_tokens": 3,
        "completion_tokens": 5,
        "total_tokens": 8
    }
}
counter.update_from_api_response(api_response, context="Hello, world!")

# 获取模型信息
model_info = counter.get_model_info()
print(f"Calibration confidence: {model_info['calibration_confidence']}")
print(f"Cache hit rate: {model_info['cache_stats']['hit_rate']}")
```

### 集成到现有系统

```python
# 在LLM调用后更新token计数器
def handle_llm_response(response: Dict[str, Any], input_text: str):
    """处理LLM响应并更新token计数器"""
    
    # 确定提供商类型
    provider = determine_provider(response)
    
    # 获取对应的计数器
    counter = get_token_counter(provider)
    
    # 更新计数器
    if counter and hasattr(counter, 'update_from_api_response'):
        success = counter.update_from_api_response(response, input_text)
        if success:
            logger.info("Token counter updated from API response")
            
            # 获取最新的使用情况
            usage = counter.get_last_api_usage()
            if usage:
                logger.info(f"API usage: prompt={usage.prompt_tokens}, "
                          f"completion={usage.completion_tokens}, "
                          f"total={usage.total_tokens}")

# 使用示例
llm_response = {
    "id": "chatcmpl-123",
    "object": "chat.completion", 
    "model": "gpt-4",
    "usage": {
        "prompt_tokens": 25,
        "completion_tokens": 15,
        "total_tokens": 40
    }
}

handle_llm_response(llm_response, "What is the capital of France?")
```

### 监控和调试

```python
def log_token_counter_stats():
    """记录所有token计数器的统计信息"""
    counters = get_all_token_counters()
    
    for provider, counter in counters.items():
        if hasattr(counter, 'get_model_info'):
            info = counter.get_model_info()
            
            logger.info(f"Token Counter Stats - {provider}:")
            logger.info(f"  Calibration confidence: {info['calibration_confidence']:.2f}")
            logger.info(f"  Cache hit rate: {info['cache_stats']['hit_rate']:.2f}")
            logger.info(f"  API usage hits: {info['api_usage_stats']['api_hits']}")
            logger.info(f"  Calibration uses: {info['api_usage_stats']['calibration_uses']}")
            
            if 'calibration_stats' in info:
                cal_stats = info['calibration_stats']
                logger.info(f"  Calibration factor: {cal_stats['calibration_factor']:.3f}")
                logger.info(f"  Data points: {cal_stats['data_points']}")
                logger.info(f"  Ratio mean: {cal_stats['ratio_mean']:.3f}")
                logger.info(f"  Ratio std: {cal_stats['ratio_std']:.3f}")

# 定期记录统计信息
import threading
def periodic_stats_logging():
    while True:
        log_token_counter_stats()
        time.sleep(300)  # 每5分钟记录一次

# 启动后台线程
stats_thread = threading.Thread(target=periodic_stats_logging, daemon=True)
stats_thread.start()
```

## 性能优化建议

### 1. 缓存优化

```python
# 配置合适的缓存参数
config = {
    "model_type": "openai",
    "model_name": "gpt-4",
    "cache_ttl": 1800,  # 30分钟TTL
    "cache_size": 500   # 最大500条缓存
}

counter = EnhancedTokenCounterFactory.create_with_config(config)
```

### 2. 批量处理

```python
def batch_update_token_counters(responses: List[Dict[str, Any]], 
                               texts: List[str],
                               provider: str):
    """批量更新token计数器"""
    counter = EnhancedTokenCounterFactory.create_counter(provider, "default")
    
    for response, text in zip(responses, texts):
        counter.update_from_api_response(response, text)
    
    return counter
```

### 3. 异步处理

```python
import asyncio

async def async_update_token_counter(counter: EnhancedTokenCounter, 
                                    response: Dict[str, Any], 
                                    context: str):
    """异步更新token计数器"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, 
        counter.update_from_api_response, 
        response, 
        context
    )
```

## 错误处理和降级策略

```python
class RobustTokenCounter:
    """健壮的token计数器包装器"""
    
    def __init__(self, counter: EnhancedTokenCounter):
        self.counter = counter
        self.fallback_enabled = True
        self.error_threshold = 5
        self._consecutive_errors = 0
    
    def count_tokens_with_fallback(self, text: str) -> int:
        """带降级的token计数"""
        try:
            # 尝试使用增强计数
            count = self.counter.count_tokens(text)
            self._consecutive_errors = 0
            return count
            
        except Exception as e:
            self._consecutive_errors += 1
            logger.error(f"Token counter error: {e}")
            
            if self.fallback_enabled and self._consecutive_errors < self.error_threshold:
                # 使用简单的字符估算作为降级
                fallback_count = len(text) // 4
                logger.warning(f"Using fallback token count: {fallback_count}")
                return fallback_count
            else:
                # 错误太多，抛出异常
                raise RuntimeError(f"Token counter failed after {self._consecutive_errors} attempts")
    
    def update_with_retry(self, response: Dict[str, Any], 
                         context: str, 
                         max_retries: int = 3) -> bool:
        """带重试的API响应更新"""
        for attempt in range(max_retries):
            try:
                return self.counter.update_from_api_response(response, context)
            except Exception as e:
                logger.warning(f"Update attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))  # 指数退避
                else:
                    logger.error(f"All update attempts failed after {max_retries} tries")
                    return False
        
        return False
```

## 测试代码

```python
import unittest
from unittest.mock import Mock, patch

class TestEnhancedTokenCounter(unittest.TestCase):
    
    def setUp(self):
        self.counter = EnhancedOpenAITokenCounter("gpt-4")
    
    def test_local_counting(self):
        """测试本地计数功能"""
        count = self.counter._local_count_tokens("Hello, world!")
        self.assertGreater(count, 0)
    
    def test_api_response_update(self):
        """测试API响应更新"""
        response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        success = self.counter.update_from_api_response(response, "Hello")
        self.assertTrue(success)
        
        # 验证缓存
        usage = self.counter.get_last_api_usage()
        self.assertIsNotNone(usage)
        self.assertEqual(usage.total_tokens, 15)
    
    def test_calibration(self):
        """测试校准功能"""
        # 添加多个校准点
        for i in range(5):
            local = (i + 1) * 10
            api = local * 1.2  # 模拟API比本地多20%
            self.counter.calibrator.add_calibration_point(local, api)
        
        # 验证校准置信度
        confidence = self.counter.calibrator.get_confidence()
        self.assertGreater(confidence, 0.5)
        
        # 验证校准效果
        calibrated = self.counter.calibrator.calibrate(100)
        self.assertEqual(calibrated, 120)  # 应该增加20%
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        # 第一次计数（缓存未命中）
        count1 = self.counter.count_tokens("Test text")
        
        # 第二次计数（应该命中缓存）
        count2 = self.counter.count_tokens("Test text")
        
        self.assertEqual(count1, count2)
        
        # 验证缓存统计
        stats = self.counter.cache.get_stats()
        self.assertGreater(stats["hit_rate"], 0)

if __name__ == '__main__':
    unittest.main()
```

## 部署建议

### 1. 渐进式部署

```python
# 阶段1：并行运行，对比验证
def parallel_token_counting(text: str):
    """并行运行传统和增强计数器"""
    traditional_counter = OpenAITokenCounter("gpt-4")
    enhanced_counter = EnhancedOpenAITokenCounter("gpt-4")
    
    traditional_count = traditional_counter.count_tokens(text)
    enhanced_count = enhanced_counter.count_tokens(text)
    
    # 记录差异
    logger.info(f"Token counting comparison - "
               f"Traditional: {traditional_count}, "
               f"Enhanced: {enhanced_count}, "
               f"Difference: {abs(traditional_count - enhanced_count)}")
    
    return enhanced_count

# 阶段2：逐步切换
def gradual_migration(text: str, use_enhanced: bool = False):
    """逐步迁移到增强计数器"""
    if use_enhanced:
        counter = EnhancedOpenAITokenCounter("gpt-4")
    else:
        counter = OpenAITokenCounter("gpt-4")
    
    return counter.count_tokens(text)
```

### 2. 配置管理

```yaml
# config.yaml
token_counter:
  enabled: true
  provider: "enhanced"  # "traditional" 或 "enhanced"
  cache:
    ttl: 3600
    size: 1000
  calibration:
    min_data_points: 3
    max_data_points: 100
  monitoring:
    enabled: true
    stats_interval: 300
```

### 3. 监控告警

```python
def check_token_counter_health():
    """检查token计数器健康状态"""
    counters = get_all_token_counters()
    
    for provider, counter in counters.items():
        if hasattr(counter, 'get_model_info'):
            info = counter.get_model_info()
            
            # 检查校准置信度
            confidence = info['calibration_confidence']
            if confidence < 0.3:
                send_alert(f"Low calibration confidence for {provider}: {confidence}")
            
            # 检查缓存命中率
            hit_rate = info['cache_stats']['hit_rate']
            if hit_rate < 0.1 and info['cache_stats']['cache_size'] > 10:
                send_alert(f"Low cache hit rate for {provider}: {hit_rate}")
```

## 总结

这些增强实现提供了以下关键功能：

1. **API响应解析**: 自动解析不同LLM提供商的token使用信息
2. **智能缓存**: 高效的token使用缓存，减少重复计算
3. **动态校准**: 基于历史API数据校准本地估算
4. **统计监控**: 全面的性能和准确性统计
5. **错误处理**: 健壮的降级和重试机制
6. **性能优化**: 支持批量处理和异步操作

通过这些实现，可以显著提高token计数的准确性，同时保持良好的性能和可靠性。