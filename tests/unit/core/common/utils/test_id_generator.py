"""IDGenerator单元测试"""

import re
import time
from src.core.common.utils.id_generator import IDGenerator


class TestIDGenerator:
    """IDGenerator测试类"""

    def test_generate_id(self):
        """测试生成ID"""
        # 测试不带前缀的ID
        id1 = IDGenerator.generate_id()
        id2 = IDGenerator.generate_id()
        
        # 验证ID格式
        assert isinstance(id1, str)
        assert isinstance(id2, str)
        assert id1 != id2  # 两次生成的ID应该不同
        
        # 验证ID包含时间戳和随机部分
        parts = id1.split('_')
        assert len(parts) == 2  # 时间戳_随机部分
        assert parts[0].isdigit()  # 时间戳部分应该是数字
        assert len(parts[1]) == 8  # 随机部分长度为8

        # 测试带前缀的ID
        id_with_prefix = IDGenerator.generate_id(prefix="test")
        assert id_with_prefix.startswith("test_")
        
        parts = id_with_prefix.split('_')
        assert len(parts) == 3  # 前缀_时间戳_随机部分
        assert parts[0] == "test"
        assert parts[1].isdigit()  # 时间戳部分
        assert len(parts[2]) == 8  # 随机部分长度为8

        # 测试自定义长度
        id_custom_length = IDGenerator.generate_id(prefix="custom", length=12)
        parts = id_custom_length.split('_')
        assert len(parts[2]) == 12  # 随机部分长度为12

    def test_generate_uuid(self):
        """测试生成UUID"""
        uuid1 = IDGenerator.generate_uuid()
        uuid2 = IDGenerator.generate_uuid()

        # 验证UUID格式
        assert isinstance(uuid1, str)
        assert isinstance(uuid2, str)
        assert uuid1 != uuid2  # 两次生成的UUID应该不同
        
        # 验证UUID格式（标准UUID格式）
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        assert re.match(uuid_pattern, uuid1)
        assert re.match(uuid_pattern, uuid2)

    def test_generate_short_uuid(self):
        """测试生成短UUID"""
        short_uuid1 = IDGenerator.generate_short_uuid()
        short_uuid2 = IDGenerator.generate_short_uuid()

        # 验证短UUID格式
        assert isinstance(short_uuid1, str)
        assert isinstance(short_uuid2, str)
        assert short_uuid1 != short_uuid2
        assert len(short_uuid1) == 8  # 默认长度为8
        assert len(short_uuid2) == 8

        # 测试自定义长度
        custom_length_uuid = IDGenerator.generate_short_uuid(length=12)
        assert len(custom_length_uuid) == 12

    def test_generate_hash(self):
        """测试生成哈希"""
        content = "test content"
        
        # 测试MD5
        md5_hash = IDGenerator.generate_hash(content, "md5")
        assert isinstance(md5_hash, str)
        assert len(md5_hash) == 32  # MD5哈希长度为32字符
        assert re.match(r'^[a-f0-9]{32}$', md5_hash)

        # 测试SHA1
        sha1_hash = IDGenerator.generate_hash(content, "sha1")
        assert isinstance(sha1_hash, str)
        assert len(sha1_hash) == 40  # SHA1哈希长度为40字符
        assert re.match(r'^[a-f0-9]{40}$', sha1_hash)

        # 测试SHA256
        sha256_hash = IDGenerator.generate_hash(content, "sha256")
        assert isinstance(sha256_hash, str)
        assert len(sha256_hash) == 64  # SHA256哈希长度为64字符
        assert re.match(r'^[a-f0-9]{64}$', sha256_hash)

        # 测试默认算法（MD5）
        default_hash = IDGenerator.generate_hash(content)
        assert default_hash == md5_hash

        # 测试不支持的算法
        try:
            IDGenerator.generate_hash(content, "unsupported")
            assert False, "应该抛出ValueError异常"
        except ValueError:
            pass  # 期望抛出异常

    def test_generate_nanoid(self):
        """测试生成NanoID"""
        nanoid1 = IDGenerator.generate_nanoid()
        nanoid2 = IDGenerator.generate_nanoid()

        # 验证NanoID格式
        assert isinstance(nanoid1, str)
        assert isinstance(nanoid2, str)
        assert nanoid1 != nanoid2
        assert len(nanoid1) == 21  # 默认长度为21
        assert len(nanoid2) == 21

        # 验证NanoID字符集
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")
        assert all(c in allowed_chars for c in nanoid1)
        assert all(c in allowed_chars for c in nanoid2)

        # 测试自定义长度
        custom_length_nanoid = IDGenerator.generate_nanoid(length=15)
        assert len(custom_length_nanoid) == 15

    def test_generate_time_based_id(self):
        """测试生成基于时间的ID"""
        time_id1 = IDGenerator.generate_time_based_id()
        time_id2 = IDGenerator.generate_time_based_id()

        # 验证时间ID格式
        assert isinstance(time_id1, str)
        assert isinstance(time_id2, str)
        assert time_id1 != time_id2  # 时间ID应该不同（基于时间戳）
        
        # 验证时间ID是数字
        assert time_id1.isdigit()
        assert time_id2.isdigit()

    def test_generate_session_id(self):
        """测试生成会话ID"""
        session_id = IDGenerator.generate_session_id()

        # 验证会话ID格式
        assert isinstance(session_id, str)
        assert session_id.startswith("session_")
        
        # 验证UUID部分
        uuid_part = session_id[8:]  # 去掉"session_"前缀
        uuid_pattern = r'^[0-9a-f]{32}$'  # UUID的hex格式
        assert re.match(uuid_pattern, uuid_part)

    def test_generate_thread_id(self):
        """测试生成线程ID"""
        thread_id = IDGenerator.generate_thread_id()

        # 验证线程ID格式
        assert isinstance(thread_id, str)
        assert thread_id.startswith("thread_")
        
        # 验证UUID部分
        uuid_part = thread_id[7:]  # 去掉"thread_"前缀
        uuid_pattern = r'^[0-9a-f]{32}$'  # UUID的hex格式
        assert re.match(uuid_pattern, uuid_part)

    def test_generate_checkpoint_id(self):
        """测试生成检查点ID"""
        checkpoint_id = IDGenerator.generate_checkpoint_id()

        # 验证检查点ID格式
        assert isinstance(checkpoint_id, str)
        assert checkpoint_id.startswith("checkpoint_")
        
        # 验证UUID部分
        uuid_part = checkpoint_id[11:]  # 去掉"checkpoint_"前缀
        uuid_pattern = r'^[0-9a-f]{32}$' # UUID的hex格式
        assert re.match(uuid_pattern, uuid_part)

    def test_generate_workflow_id(self):
        """测试生成工作流ID"""
        workflow_id = IDGenerator.generate_workflow_id()

        # 验证工作流ID格式
        assert isinstance(workflow_id, str)
        assert workflow_id.startswith("workflow_")
        
        # 验证UUID部分
        uuid_part = workflow_id[9:]  # 去掉"workflow_"前缀
        uuid_pattern = r'^[0-9a-f]{32}$'  # UUID的hex格式
        assert re.match(uuid_pattern, uuid_part)

    def test_id_uniqueness(self):
        """测试ID唯一性"""
        ids = set()
        for _ in range(100):
            ids.add(IDGenerator.generate_id())
        
        # 验证所有生成的ID都是唯一的
        assert len(ids) == 100