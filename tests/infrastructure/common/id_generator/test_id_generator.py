"""ID生成器测试"""

import pytest
import re
import time
from src.infrastructure.common.id_generator.id_generator import IDGenerator


class TestIDGenerator:
    """ID生成器测试类"""
    
    def test_generate_id(self):
        """测试生成ID"""
        id1 = IDGenerator.generate_id()
        id2 = IDGenerator.generate_id()
        
        # 确保ID是唯一的
        assert id1 != id2
        
        # 检查格式
        assert isinstance(id1, str)
        assert len(id1) > 0
        
        # 检查包含时间戳和随机部分
        parts = id1.split('_')
        assert len(parts) >= 2
    
    def test_generate_id_with_prefix(self):
        """测试生成带前缀的ID"""
        id1 = IDGenerator.generate_id(prefix="test")
        id2 = IDGenerator.generate_id(prefix="test")
        
        # 确保ID是唯一的
        assert id1 != id2
        
        # 检查前缀
        assert id1.startswith("test_")
        assert id2.startswith("test_")
    
    def test_generate_id_with_length(self):
        """测试生成指定长度的ID"""
        id1 = IDGenerator.generate_id(length=4)
        id2 = IDGenerator.generate_id(length=12)
        
        parts1 = id1.split('_')
        parts2 = id2.split('_')
        
        # 检查随机部分长度
        assert len(parts1[-1]) == 4
        assert len(parts2[-1]) == 12
    
    def test_generate_uuid(self):
        """测试生成UUID"""
        uuid1 = IDGenerator.generate_uuid()
        uuid2 = IDGenerator.generate_uuid()
        
        # 确保UUID是唯一的
        assert uuid1 != uuid2
        
        # 检查格式
        assert isinstance(uuid1, str)
        assert len(uuid1) == 36  # 标准UUID长度
        
        # 检查包含连字符
        assert '-' in uuid1
        
        # 检查格式模式
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        assert uuid_pattern.match(uuid1) is not None
    
    def test_generate_short_uuid(self):
        """测试生成短UUID"""
        short_uuid1 = IDGenerator.generate_short_uuid()
        short_uuid2 = IDGenerator.generate_short_uuid()
        
        # 确保短UUID是唯一的
        assert short_uuid1 != short_uuid2
        
        # 检查长度
        assert len(short_uuid1) == 8
        assert len(short_uuid2) == 8
        
        # 检查只包含十六进制字符
        hex_pattern = re.compile(r'^[0-9a-f]+$', re.IGNORECASE)
        assert hex_pattern.match(short_uuid1) is not None
    
    def test_generate_short_uuid_with_length(self):
        """测试生成指定长度的短UUID"""
        short_uuid = IDGenerator.generate_short_uuid(length=12)
        assert len(short_uuid) == 12
    
    def test_generate_hash_md5(self):
        """测试生成MD5哈希"""
        content = "test content"
        hash1 = IDGenerator.generate_hash(content, "md5")
        hash2 = IDGenerator.generate_hash(content, "md5")
        
        # 相同内容应该生成相同哈希
        assert hash1 == hash2
        
        # 检查长度
        assert len(hash1) == 32  # MD5哈希长度
        
        # 检查只包含十六进制字符
        hex_pattern = re.compile(r'^[0-9a-f]+$', re.IGNORECASE)
        assert hex_pattern.match(hash1) is not None
    
    def test_generate_hash_sha1(self):
        """测试生成SHA1哈希"""
        content = "test content"
        hash1 = IDGenerator.generate_hash(content, "sha1")
        hash2 = IDGenerator.generate_hash(content, "sha1")
        
        # 相同内容应该生成相同哈希
        assert hash1 == hash2
        
        # 检查长度
        assert len(hash1) == 40  # SHA1哈希长度
        
        # 检查只包含十六进制字符
        hex_pattern = re.compile(r'^[0-9a-f]+$', re.IGNORECASE)
        assert hex_pattern.match(hash1) is not None
    
    def test_generate_hash_sha256(self):
        """测试生成SHA256哈希"""
        content = "test content"
        hash1 = IDGenerator.generate_hash(content, "sha256")
        hash2 = IDGenerator.generate_hash(content, "sha256")
        
        # 相同内容应该生成相同哈希
        assert hash1 == hash2
        
        # 检查长度
        assert len(hash1) == 64  # SHA256哈希长度
        
        # 检查只包含十六进制字符
        hex_pattern = re.compile(r'^[0-9a-f]+$', re.IGNORECASE)
        assert hex_pattern.match(hash1) is not None
    
    def test_generate_hash_different_content(self):
        """测试不同内容生成不同哈希"""
        content1 = "content1"
        content2 = "content2"
        
        hash1 = IDGenerator.generate_hash(content1, "md5")
        hash2 = IDGenerator.generate_hash(content2, "md5")
        
        # 不同内容应该生成不同哈希
        assert hash1 != hash2
    
    def test_generate_hash_invalid_algorithm(self):
        """测试无效哈希算法"""
        with pytest.raises(ValueError):
            IDGenerator.generate_hash("test", "invalid")
    
    def test_generate_nanoid(self):
        """测试生成NanoID"""
        nanoid1 = IDGenerator.generate_nanoid()
        nanoid2 = IDGenerator.generate_nanoid()
        
        # 确保NanoID是唯一的
        assert nanoid1 != nanoid2
        
        # 检查长度
        assert len(nanoid1) == 21  # 默认长度
        
        # 检查只包含URL安全字符
        nanoid_pattern = re.compile(r'^[A-Za-z0-9_-]+$')
        assert nanoid_pattern.match(nanoid1) is not None
    
    def test_generate_time_based_id(self):
        """测试生成基于时间的ID"""
        id1 = IDGenerator.generate_time_based_id()
        time.sleep(0.001)  # 确保时间差异
        id2 = IDGenerator.generate_time_based_id()
        
        # 确保ID是唯一的
        assert id1 != id2
        
        # 检查格式
        assert isinstance(id1, str)
        assert id1.isdigit()
        
        # 检查时间顺序
        assert int(id2) > int(id1)
    
    def test_generate_session_id(self):
        """测试生成会话ID"""
        session_id1 = IDGenerator.generate_session_id()
        session_id2 = IDGenerator.generate_session_id()
        
        # 确保会话ID是唯一的
        assert session_id1 != session_id2
        
        # 检查前缀
        assert session_id1.startswith("session_")
        assert session_id2.startswith("session_")
        
        # 检查长度
        assert len(session_id1) > len("session_")
    
    def test_generate_thread_id(self):
        """测试生成线程ID"""
        thread_id1 = IDGenerator.generate_thread_id()
        thread_id2 = IDGenerator.generate_thread_id()
        
        # 确保线程ID是唯一的
        assert thread_id1 != thread_id2
        
        # 检查前缀
        assert thread_id1.startswith("thread_")
        assert thread_id2.startswith("thread_")
        
        # 检查长度
        assert len(thread_id1) > len("thread_")
    
    def test_generate_checkpoint_id(self):
        """测试生成检查点ID"""
        checkpoint_id1 = IDGenerator.generate_checkpoint_id()
        checkpoint_id2 = IDGenerator.generate_checkpoint_id()
        
        # 确保检查点ID是唯一的
        assert checkpoint_id1 != checkpoint_id2
        
        # 检查前缀
        assert checkpoint_id1.startswith("checkpoint_")
        assert checkpoint_id2.startswith("checkpoint_")
        
        # 检查长度
        assert len(checkpoint_id1) > len("checkpoint_")
    
    def test_generate_workflow_id(self):
        """测试生成工作流ID"""
        workflow_id1 = IDGenerator.generate_workflow_id()
        workflow_id2 = IDGenerator.generate_workflow_id()
        
        # 确保工作流ID是唯一的
        assert workflow_id1 != workflow_id2
        
        # 检查前缀
        assert workflow_id1.startswith("workflow_")
        assert workflow_id2.startswith("workflow_")
        
        # 检查长度
        assert len(workflow_id1) > len("workflow_")
    
    def test_id_uniqueness_across_types(self):
        """测试不同类型ID的唯一性"""
        # 生成各种类型的ID
        generic_id = IDGenerator.generate_id()
        uuid = IDGenerator.generate_uuid()
        short_uuid = IDGenerator.generate_short_uuid()
        nanoid = IDGenerator.generate_nanoid()
        time_based_id = IDGenerator.generate_time_based_id()
        session_id = IDGenerator.generate_session_id()
        thread_id = IDGenerator.generate_thread_id()
        checkpoint_id = IDGenerator.generate_checkpoint_id()
        workflow_id = IDGenerator.generate_workflow_id()
        
        # 收集所有ID
        all_ids = [
            generic_id, uuid, short_uuid, nanoid, time_based_id,
            session_id, thread_id, checkpoint_id, workflow_id
        ]
        
        # 确保所有ID都是唯一的
        assert len(all_ids) == len(set(all_ids))
    
    def test_id_consistency(self):
        """测试ID生成的一致性"""
        # 测试相同参数生成的ID格式一致
        for _ in range(10):
            session_id = IDGenerator.generate_session_id()
            assert session_id.startswith("session_")
            assert len(session_id) == len("session_") + 32  # session_ + UUID hex