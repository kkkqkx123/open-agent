"""测试TokenUsage数据类型"""

import pytest
from datetime import datetime
from src.services.llm.token_processing.token_types import TokenUsage


class TestTokenUsage:
    """测试TokenUsage类"""
    
    def test_default_initialization(self):
        """测试默认初始化"""
        usage = TokenUsage()
        
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0
        assert usage.source == "local"
        assert usage.timestamp is not None
        assert usage.additional_info == {}
    
    def test_custom_initialization(self):
        """测试自定义初始化"""
        timestamp = datetime.now()
        additional_info = {"model": "gpt-4", "cost": 0.01}
        
        usage = TokenUsage(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            source="api",
            timestamp=timestamp,
            additional_info=additional_info
        )
        
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.total_tokens == 30
        assert usage.source == "api"
        assert usage.timestamp == timestamp
        assert usage.additional_info == additional_info
    
    def test_is_from_api(self):
        """测试is_from_api属性"""
        api_usage = TokenUsage(source="api")
        local_usage = TokenUsage(source="local")
        
        assert api_usage.is_from_api is True
        assert local_usage.is_from_api is False
    
    def test_is_from_local(self):
        """测试is_from_local属性"""
        api_usage = TokenUsage(source="api")
        local_usage = TokenUsage(source="local")
        
        assert api_usage.is_from_local is False
        assert local_usage.is_from_local is True
    
    def test_add(self):
        """测试add方法"""
        usage1 = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        usage2 = TokenUsage(prompt_tokens=20, completion_tokens=10, total_tokens=30)
        
        result = usage1.add(usage2)
        
        assert result.prompt_tokens == 30
        assert result.completion_tokens == 15
        assert result.total_tokens == 45
        assert result.source == usage1.source  # 保持原有的source
        assert result.timestamp == usage1.timestamp  # 保持原有的timestamp
    
    def test_copy(self):
        """测试copy方法"""
        timestamp = datetime.now()
        additional_info = {"model": "gpt-4"}
        
        original = TokenUsage(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            source="api",
            timestamp=timestamp,
            additional_info=additional_info
        )
        
        copied = original.copy()
        
        # 验证所有字段都相同
        assert copied.prompt_tokens == original.prompt_tokens
        assert copied.completion_tokens == original.completion_tokens
        assert copied.total_tokens == original.total_tokens
        assert copied.source == original.source
        assert copied.timestamp == original.timestamp
        assert copied.additional_info == original.additional_info
        
        # 验证是不同的对象
        assert copied is not original
        assert copied.additional_info is not original.additional_info
    
    def test_to_dict(self):
        """测试to_dict方法"""
        timestamp = datetime.now()
        additional_info = {"model": "gpt-4"}
        
        usage = TokenUsage(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            source="api",
            timestamp=timestamp,
            additional_info=additional_info
        )
        
        result = usage.to_dict()
        
        assert result["prompt_tokens"] == 10
        assert result["completion_tokens"] == 5
        assert result["total_tokens"] == 15
        assert result["source"] == "api"
        assert result["timestamp"] == timestamp.isoformat()
        assert result["additional_info"] == additional_info
    
    def test_from_dict(self):
        """测试from_dict方法"""
        timestamp = datetime.now()
        additional_info = {"model": "gpt-4"}
        
        data = {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
            "source": "api",
            "timestamp": timestamp.isoformat(),
            "additional_info": additional_info
        }
        
        usage = TokenUsage.from_dict(data)
        
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 5
        assert usage.total_tokens == 15
        assert usage.source == "api"
        assert usage.timestamp == timestamp
        assert usage.additional_info == additional_info
    
    def test_from_dict_with_missing_fields(self):
        """测试from_dict方法处理缺失字段"""
        data = {
            "prompt_tokens": 10,
            "completion_tokens": 5
            # 缺失其他字段
        }
        
        usage = TokenUsage.from_dict(data)
        
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 5
        assert usage.total_tokens == 0  # 默认值
        assert usage.source == "local"  # 默认值
        assert usage.timestamp is not None  # 自动生成
        assert usage.additional_info is None  # 缺失字段
    
    def test_from_dict_with_none_timestamp(self):
        """测试from_dict方法处理None时间戳"""
        data = {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
            "timestamp": None
        }
        
        usage = TokenUsage.from_dict(data)
        
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 5
        assert usage.total_tokens == 15
        assert usage.timestamp is None