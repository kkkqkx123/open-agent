"""Checkpoint模块集成测试
"""

import asyncio
import tempfile
import os
from pathlib import Path

from src.core.checkpoints.exceptions import CheckpointError
from src.services.checkpoint.manager import CheckpointManager
from src.services.checkpoint.serializer import CheckpointSerializer
from src.adapters.storage.backends.checkpoint.memory import CheckpointMemoryBackend
from src.adapters.storage.backends.checkpoint.sqlite import CheckpointSqliteBackend
from src.adapters.storage.backends.checkpoint.langgraph import LangGraphCheckpointAdapter
from src.adapters.storage.factory import StorageAdapterFactory, create_storage_adapter
from src.adapters.storage.registry import storage_registry


async def test_checkpoint_integration():
    """测试checkpoint模块集成"""
    print("开始测试checkpoint模块集成...")
    
    # 测试1: 验证异常类
    print("\n1. 测试异常类...")
    try:
        from src.core.checkpoints.exceptions import (
            CheckpointError,
            CheckpointNotFoundError,
            CheckpointStorageError,
            CheckpointValidationError
        )
        print("✓ 异常类导入成功")
    except ImportError as e:
        print(f"✗ 异常类导入失败: {e}")
        return False
    
    # 测试2: 验证实体类
    print("\n2. 测试实体类...")
    try:
        from src.core.checkpoints.entities import CheckpointData, CheckpointConfig
        print("✓ 实体类导入成功")
    except ImportError as e:
        print(f"✗ 实体类导入失败: {e}")
        return False
    
    # 测试3: 验证服务类
    print("\n3. 测试服务类...")
    try:
        manager = CheckpointManager()
        serializer = CheckpointSerializer()
        print("✓ 服务类实例化成功")
    except Exception as e:
        print(f"✗ 服务类实例化失败: {e}")
        return False
    
    # 测试4: 验证存储后端
    print("\n4. 测试存储后端...")
    try:
        # 内存后端
        memory_backend = CheckpointMemoryBackend()
        await memory_backend.connect()
        print("✓ 内存后端连接成功")
        
        # SQLite后端
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            tmp_db_path = tmp_file.name
        
        try:
            sqlite_backend = CheckpointSqliteBackend(db_path=tmp_db_path)
            await sqlite_backend.connect()
            print("✓ SQLite后端连接成功")
            
            # 断开连接
            await sqlite_backend.disconnect()
        finally:
            # 清理临时文件
            if os.path.exists(tmp_db_path):
                os.remove(tmp_db_path)
        
        print("✓ 存储后端测试成功")
    except Exception as e:
        print(f"✗ 存储后端测试失败: {e}")
        return False
    
    # 测试5: 验证工厂和注册表
    print("\n5. 测试工厂和注册表...")
    try:
        # 检查注册的存储类型
        registered_types = storage_registry.get_registered_types()
        print(f"✓ 注册的存储类型: {registered_types}")
        
        # 检查checkpoint相关类型是否已注册
        checkpoint_types = [t for t in registered_types if 'checkpoint' in t or t == 'langgraph']
        if checkpoint_types:
            print(f"✓ Checkpoint相关类型已注册: {checkpoint_types}")
        else:
            print("✗ Checkpoint相关类型未注册")
            return False
        
        # 测试创建适配器
        factory = StorageAdapterFactory()
        supported_types = factory.get_supported_types()
        print(f"✓ 支持的存储类型: {supported_types}")
        
        print("✓ 工厂和注册表测试成功")
    except Exception as e:
        print(f"✗ 工厂和注册表测试失败: {e}")
        return False
    
    # 测试6: 验证LangGraph适配器
    print("\n6. 测试LangGraph适配器...")
    try:
        # 创建一个模拟的checkpointer（由于我们没有实际的LangGraph环境）
        class MockCheckpointer:
            def put(self, config, checkpoint, metadata, new_versions):
                pass
            
            def get(self, config):
                return None
            
            def list(self, config, limit=None):
                return []
        
        langgraph_adapter = LangGraphCheckpointAdapter(MockCheckpointer())
        print("✓ LangGraph适配器实例化成功")
    except Exception as e:
        print(f"✗ LangGraph适配器实例化失败: {e}")
        return False
    
    print("\n✓ 所有集成测试通过！")
    return True


def test_serialization():
    """测试序列化功能"""
    print("\n7. 测试序列化功能...")
    try:
        serializer = CheckpointSerializer()
        
        # 测试工作流状态序列化
        test_state = {"message": "Hello, World!", "count": 42}
        serialized = serializer.serialize_workflow_state(test_state)
        deserialized = serializer.deserialize_workflow_state(serialized)
        
        if deserialized == test_state:
            print("✓ 工作流状态序列化/反序列化成功")
        else:
            print("✗ 工作流状态序列化/反序列化失败")
            return False
        
        # 测试消息序列化
        test_messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]
        serialized_msgs = serializer.serialize_messages(test_messages)
        deserialized_msgs = serializer.deserialize_messages(serialized_msgs)
        
        if deserialized_msgs == test_messages:
            print("✓ 消息序列化/反序列化成功")
        else:
            print("✗ 消息序列化/反序列化失败")
            return False
        
        # 测试工具结果序列化
        test_tool_results = {"result": "success", "data": {"value": 123}}
        serialized_tools = serializer.serialize_tool_results(test_tool_results)
        deserialized_tools = serializer.deserialize_tool_results(serialized_tools)
        
        if deserialized_tools == test_tool_results:
            print("✓ 工具结果序列化/反序列化成功")
        else:
            print("✗ 工具结果序列化/反序列化失败")
            return False
        
        print("✓ 序列化功能测试成功")
        return True
    except Exception as e:
        print(f"✗ 序列化功能测试失败: {e}")
        return False


async def main():
    """主函数"""
    print("开始执行checkpoint模块集成测试...")
    
    # 执行异步测试
    success1 = await test_checkpoint_integration()
    
    # 执行同步测试
    success2 = test_serialization()
    
    if success1 and success2:
        print("\n🎉 所有测试通过！Checkpoint模块迁移成功。")
        return True
    else:
        print("\n❌ 部分测试失败。")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)