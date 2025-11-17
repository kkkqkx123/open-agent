"""Token类型测试"""

import pytest
from datetime import datetime
from src.services.llm.token_processing.token_types import TokenUsage


class TestTokenUsage:
    """TokenUsage类测试"""
    
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
        additional_info = {"model": "gpt-4", "cost": 0.001}
        
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
    
    def test_post_init(self):
        """测试后处理方法"""
        usage = TokenUsage()
        
        # 检查timestamp是否自动设置
        assert isinstance(usage.timestamp, datetime)
        
        # 检查additional_info是否自动初始化
        assert usage.additional_info == {}
    
    def test_is_from_api(self):
        """测试API来源检查"""
        api_usage = TokenUsage(source="api")
        local_usage = TokenUsage(source="local")
        
        assert api_usage.is_from_api is True
        assert api_usage.is_from_local is False
        assert local_usage.is_from_api is False
        assert local_usage.is_from_local is True
    
    def test_add(self):
        """测试TokenUsage相加"""
        usage1 = TokenUsage(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            source="api"
        )
        
        usage2 = TokenUsage(
            prompt_tokens=5,
            completion_tokens=15,
            total_tokens=20,
            source="local"
        )
        
        result = usage1.add(usage2)
        
        assert result.prompt_tokens == 15
        assert result.completion_tokens == 35
        assert result.total_tokens == 50
        assert result.source == "api"  # 保持第一个usage的source
        assert result.timestamp == usage1.timestamp  # 保持第一个usage的timestamp
    
    def test_copy(self):
        """测试TokenUsage复制"""
        original = TokenUsage(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            source="api",
            additional_info={"model": "gpt-4"}
        )
        
        copied = original.copy()
        
        # 检查所有字段都相同
        assert copied.prompt_tokens == original.prompt_tokens
        assert copied.completion_tokens == original.completion_tokens
        assert copied.total_tokens == original.total_tokens
        assert copied.source == original.source
        assert copied.timestamp == original.timestamp
        assert copied.additional_info == original.additional_info
        
        # 检查是不同的对象
        assert copied is not original
        assert copied.additional_info is not original.additional_info
    
    def test_to_dict(self):
        """测试转换为字典"""
        timestamp = datetime.now()
        usage = TokenUsage(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            source="api",
            timestamp=timestamp,
            additional_info={"model": "gpt-4"}
        )
        
        result = usage.to_dict()
        
        expected = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
            "source": "api",
            "timestamp": timestamp.isoformat(),
            "additional_info": {"model": "gpt-4"}
        }
        
        assert result == expected
    
    def test_from_dict(self):
        """测试从字典创建"""
        timestamp = datetime.now()
        data = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
            "source": "api",
            "timestamp": timestamp.isoformat(),
            "additional_info": {"model": "gpt-4"}
        }
        
        usage = TokenUsage.from_dict(data)
        
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.total_tokens == 30
        assert usage.source == "api"
        assert usage.timestamp == timestamp
        assert usage.additional_info == {"model": "gpt-4"}
    
    def test_from_dict_with_missing_fields(self):
        """测试从缺少字段的字典创建"""
        data = {
            "prompt_tokens": 10,
            "completion_tokens": 20
            # 缺少其他字段
        }
        
        usage = TokenUsage.from_dict(data)
        
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.total_tokens == 0  # 默认值
        assert usage.source == "local"  # 默认值
        assert usage.timestamp is not None  # 自动生成
        assert usage.additional_info is None  # 默认值
    
    def test_from_dict_with_none_timestamp(self):
        """测试从包含None时间戳的字典创建"""
        data = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "timestamp": None
        }
        
        usage = TokenUsage.from_dict(data)
        
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.timestamp is None
    
    def test_roundtrip_serialization(self):
        """测试往返序列化"""
        original = TokenUsage(
            prompt_tokens=15,
            completion_tokens=25,
            total_tokens=40,
            source="api",
            additional_info={"model": "gpt-4", "cost": 0.002}
        )
        
        # 转换为字典再转换回来
        dict_data = original.to_dict()
        restored = TokenUsage.from_dict(dict_data)
        
        # 检查所有字段都相同
        assert restored.prompt_tokens == original.prompt_tokens
        assert restored.completion_tokens == original.completion_tokens
        assert restored.total_tokens == original.total_tokens
        assert restored.source == original.source
        assert restored.additional_info == original.additional_info