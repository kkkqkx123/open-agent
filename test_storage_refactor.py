"""测试存储重构后的功能

验证新的通用工具类和优化基类是否正常工作。
"""

import asyncio
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from adapters.storage.utils.common_utils import StorageCommonUtils
from adapters.storage.utils.memory_utils import MemoryStorageUtils
from adapters.storage.utils.sqlite_utils import SQLiteStorageUtils
from adapters.storage.utils.file_utils import FileStorageUtils


async def test_common_utils():
    """测试通用工具类"""
    print("=== 测试通用工具类 ===")
    
    # 测试数据压缩/解压缩
    test_data = {"key": "value", "number": 123, "nested": {"inner": "data"}}
    
    compressed = StorageCommonUtils.compress_data(test_data)
    print(f"压缩数据大小: {len(compressed)} 字节")
    
    decompressed = StorageCommonUtils.decompress_data(compressed)
    print(f"解压缩数据: {decompressed}")
    assert decompressed == test_data, "压缩/解压缩失败"
    
    # 测试序列化/反序列化
    serialized = StorageCommonUtils.serialize_data(test_data)
    print(f"序列化数据: {serialized}")
    
    deserialized = StorageCommonUtils.deserialize_data(serialized)
    assert deserialized == test_data, "序列化/反序列化失败"
    
    # 测试过滤器匹配
    filters = {"key": "value", "number": {"$gt": 100}}
    assert StorageCommonUtils.matches_filters(test_data, filters), "过滤器匹配失败"
    
    # 测试过期检查
    expired_data = {"expires_at": time.time() - 1000}
    assert StorageCommonUtils.is_data_expired(expired_data), "过期检查失败"
    
    # 测试时间戳生成
    timestamp_file = StorageCommonUtils.generate_timestamp_filename("test", "txt")
    print(f"时间戳文件名: {timestamp_file}")
    assert timestamp_file.startswith("test_"), "时间戳文件名生成失败"
    
    print("✓ 通用工具类测试通过")


async def test_memory_utils():
    """测试内存存储工具类"""
    print("\n=== 测试内存存储工具类 ===")
    
    # 测试容量验证
    test_storage = {"item1": "data1", "item2": "data2"}
    
    try:
        MemoryStorageUtils.validate_capacity(test_storage, max_size=1)
        assert False, "容量验证应该失败"
    except Exception as e:
        print(f"✓ 容量验证正确失败: {e}")
    
    # 测试内存使用量计算
    memory_usage = MemoryStorageUtils.calculate_memory_usage(test_storage)
    print(f"内存使用量: {memory_usage} 字节")
    assert memory_usage > 0, "内存使用量计算失败"
    
    print("✓ 内存存储工具类测试通过")


async def test_sqlite_utils():
    """测试SQLite存储工具类"""
    print("\n=== 测试SQLite存储工具类 ===")
    
    # 测试WHERE子句构建
    filters = {"type": "test", "age": {"$gt": 18}, "status": ["active", "pending"]}
    where_clause, params = SQLiteStorageUtils.build_where_clause(filters)
    print(f"WHERE子句: {where_clause}")
    print(f"参数: {params}")
    
    assert "type = ?" in where_clause, "WHERE子句构建失败"
    assert "age > ?" in where_clause, "WHERE子句构建失败"
    assert "status IN" in where_clause, "WHERE子句构建失败"
    
    print("✓ SQLite存储工具类测试通过")


async def test_file_utils():
    """测试文件存储工具类"""
    print("\n=== 测试文件存储工具类 ===")
    
    # 测试文件列表
    test_dir = "test_temp_dir"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建测试文件
    test_file = os.path.join(test_dir, "test.json")
    test_data = {"test": "data"}
    
    FileStorageUtils.save_data_to_file(test_file, test_data)
    assert os.path.exists(test_file), "文件保存失败"
    
    loaded_data = FileStorageUtils.load_data_from_file(test_file)
    assert loaded_data == test_data, "文件加载失败"
    
    # 测试文件存在检查
    assert FileStorageUtils.file_exists(test_file), "文件存在检查失败"
    
    # 测试文件大小
    file_size = FileStorageUtils.get_file_size(test_file)
    print(f"文件大小: {file_size} 字节")
    assert file_size > 0, "文件大小计算失败"
    
    # 清理测试文件
    os.remove(test_file)
    os.rmdir(test_dir)
    
    print("✓ 文件存储工具类测试通过")


async def main():
    """主测试函数"""
    print("开始测试存储重构后的功能...")
    
    try:
        await test_common_utils()
        await test_memory_utils()
        await test_sqlite_utils()
        await test_file_utils()
        
        print("\n🎉 所有测试通过！存储重构成功。")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import time
    success = asyncio.run(main())
    sys.exit(0 if success else 1)