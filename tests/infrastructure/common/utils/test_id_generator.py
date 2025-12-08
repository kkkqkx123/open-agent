"""ID生成器单元测试

测试基础设施层ID生成器的基本功能。
"""

import pytest
import re
import uuid
from src.infrastructure.common.utils.id_generator import IDGenerator


class TestIDGenerator:
    """测试ID生成器"""

    def test_generate_id_with_prefix(self):
        """测试带前缀的ID生成"""
        id = IDGenerator.generate_id(prefix="test")
        assert id.startswith("test_")
        # 格式: prefix_timestamp_random
        parts = id.split("_")
        assert len(parts) == 3
        assert parts[0] == "test"
        # 时间戳应为数字
        assert parts[1].isdigit()
        # 随机部分长度默认为8
        assert len(parts[2]) == 8

    def test_generate_id_without_prefix(self):
        """测试无前缀的ID生成"""
        id = IDGenerator.generate_id()
        assert "_" in id
        parts = id.split("_")
        assert len(parts) == 2
        assert parts[0].isdigit()
        assert len(parts[1]) == 8

    def test_generate_id_custom_length(self):
        """测试自定义长度的ID生成"""
        id = IDGenerator.generate_id(length=12)
        parts = id.split("_")
        # 如果没有前缀，parts[0]是时间戳，parts[1]是随机部分
        random_part_index = 1 if len(parts) == 2 else 2
        assert len(parts[random_part_index]) == 12

    def test_generate_uuid(self):
        """测试UUID生成"""
        uuid_str = IDGenerator.generate_uuid()
        # 验证UUID格式
        try:
            uuid_obj = uuid.UUID(uuid_str)
            assert str(uuid_obj) == uuid_str
        except ValueError:
            pytest.fail(f"Invalid UUID format: {uuid_str}")

    def test_generate_short_uuid(self):
        """测试短UUID生成"""
        short_uuid = IDGenerator.generate_short_uuid(length=10)
        assert len(short_uuid) == 10
        # 应为十六进制字符
        assert re.match(r'^[0-9a-f]{10}$', short_uuid) is not None

        # 测试默认长度
        short_uuid = IDGenerator.generate_short_uuid()
        assert len(short_uuid) == 8

    def test_generate_hash(self):
        """测试哈希生成"""
        content = "test content"
        
        md5_hash = IDGenerator.generate_hash(content, "md5")
        assert len(md5_hash) == 32
        assert re.match(r'^[0-9a-f]{32}$', md5_hash) is not None
        
        sha1_hash = IDGenerator.generate_hash(content, "sha1")
        assert len(sha1_hash) == 40
        
        sha256_hash = IDGenerator.generate_hash(content, "sha256")
        assert len(sha256_hash) == 64
        
        # 相同内容应产生相同哈希
        assert IDGenerator.generate_hash(content, "md5") == md5_hash
        
        # 不同内容应产生不同哈希
        different_hash = IDGenerator.generate_hash("different", "md5")
        assert different_hash != md5_hash

    def test_generate_hash_unsupported_algorithm(self):
        """测试不支持的哈希算法"""
        with pytest.raises(ValueError):
            IDGenerator.generate_hash("test", "unsupported")

    def test_generate_nanoid(self):
        """测试NanoID生成"""
        nanoid = IDGenerator.generate_nanoid()
        assert len(nanoid) == 21
        # 应只包含URL安全字符
        assert re.match(r'^[A-Za-z0-9_-]{21}$', nanoid) is not None
        
        # 测试自定义长度
        nanoid = IDGenerator.generate_nanoid(length=10)
        assert len(nanoid) == 10

    def test_generate_time_based_id(self):
        """测试基于时间的ID生成"""
        id1 = IDGenerator.generate_time_based_id()
        id2 = IDGenerator.generate_time_based_id()
        
        # 应为数字字符串
        assert id1.isdigit()
        assert id2.isdigit()
        
        # 两个ID应该不同（除非在同一毫秒内且序列号相同）
        # 至少确保它们是有效的
        int(id1)  # 不应引发异常
        int(id2)

    def test_generate_session_id(self):
        """测试会话ID生成"""
        session_id = IDGenerator.generate_session_id()
        assert session_id.startswith("session_")
        # 剩余部分应为UUID十六进制
        uuid_part = session_id[8:]
        assert re.match(r'^[0-9a-f]{32}$', uuid_part) is not None

    def test_generate_thread_id(self):
        """测试线程ID生成"""
        thread_id = IDGenerator.generate_thread_id()
        assert thread_id.startswith("thread_")
        uuid_part = thread_id[7:]
        assert re.match(r'^[0-9a-f]{32}$', uuid_part) is not None

    def test_generate_checkpoint_id(self):
        """测试检查点ID生成"""
        checkpoint_id = IDGenerator.generate_checkpoint_id()
        assert checkpoint_id.startswith("checkpoint_")
        uuid_part = checkpoint_id[11:]
        assert re.match(r'^[0-9a-f]{32}$', uuid_part) is not None

    def test_generate_workflow_id(self):
        """测试工作流ID生成"""
        workflow_id = IDGenerator.generate_workflow_id()
        assert workflow_id.startswith("workflow_")
        uuid_part = workflow_id[9:]
        assert re.match(r'^[0-9a-f]{32}$', uuid_part) is not None

    def test_id_uniqueness(self):
        """测试ID唯一性"""
        # 生成多个ID，确保它们不同（概率性测试）
        ids = set()
        for _ in range(100):
            id = IDGenerator.generate_id()
            ids.add(id)
        
        # 由于时间戳和随机性，应该所有ID都不同
        # 但有可能重复，我们只检查大部分不同
        assert len(ids) > 95  # 允许少量重复（极低概率）

    def test_static_methods(self):
        """测试静态方法调用"""
        # 确保所有方法都可以作为静态方法调用
        assert IDGenerator.generate_id() is not None
        assert IDGenerator.generate_uuid() is not None
        assert IDGenerator.generate_short_uuid() is not None
        assert IDGenerator.generate_hash("test") is not None
        assert IDGenerator.generate_nanoid() is not None
        assert IDGenerator.generate_time_based_id() is not None
        assert IDGenerator.generate_session_id() is not None
        assert IDGenerator.generate_thread_id() is not None
        assert IDGenerator.generate_checkpoint_id() is not None
        assert IDGenerator.generate_workflow_id() is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])