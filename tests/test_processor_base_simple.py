"""简化的处理器基类测试

直接测试处理器基类功能，避免复杂的依赖问题。
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def test_processor_imports():
    """测试处理器导入"""
    try:
        from src.infrastructure.config.processor.base_processor import BaseConfigProcessor, IConfigProcessor
        from src.infrastructure.config.processor.environment_processor import EnvironmentProcessor
        from src.infrastructure.config.processor.reference_processor import ReferenceProcessor
        print("✅ 处理器导入成功")
        return True
    except Exception as e:
        print(f"❌ 处理器导入失败: {e}")
        return False

def test_base_processor_functionality():
    """测试基类功能"""
    try:
        from src.infrastructure.config.processor.base_processor import BaseConfigProcessor, IConfigProcessor
        
        # 创建一个测试处理器
        class TestProcessor(BaseConfigProcessor):
            def _process_internal(self, config, config_path):
                return {"processed": True, **config}
        
        processor = TestProcessor("test")
        
        # 测试基本功能
        assert processor.get_name() == "test"
        assert processor.is_enabled()
        
        # 测试启用/禁用
        processor.set_enabled(False)
        assert not processor.is_enabled()
        
        processor.set_enabled(True)
        assert processor.is_enabled()
        
        # 测试处理功能
        test_config = {"key": "value"}
        result = processor.process(test_config, "test.yaml")
        
        assert result["processed"] is True
        assert result["key"] == "value"
        
        # 测试元数据
        processor.set_metadata("test", "value")
        assert processor.get_metadata("test") == "value"
        
        # 测试性能统计
        stats = processor.get_performance_stats()
        assert "total_calls" in stats
        assert stats["total_calls"] == 1
        
        print("✅ 基类功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 基类功能测试失败: {e}")
        return False

def test_environment_processor():
    """测试环境变量处理器"""
    try:
        from src.infrastructure.config.processor.environment_processor import EnvironmentProcessor
        
        processor = EnvironmentProcessor()
        
        # 测试基本功能
        assert processor.get_name() == "environment"
        assert processor.is_enabled()
        
        # 测试处理功能
        test_config = {"key": "value"}
        result = processor.process(test_config, "test.yaml")
        
        assert isinstance(result, dict)
        assert "key" in result
        
        print("✅ 环境变量处理器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 环境变量处理器测试失败: {e}")
        return False

def test_reference_processor():
    """测试引用处理器"""
    try:
        from src.infrastructure.config.processor.reference_processor import ReferenceProcessor
        
        processor = ReferenceProcessor()
        
        # 测试基本功能
        assert processor.get_name() == "reference"
        assert processor.is_enabled()
        
        # 测试处理功能
        test_config = {"key": "value"}
        result = processor.process(test_config, "test.yaml")
        
        assert isinstance(result, dict)
        assert "key" in result
        
        print("✅ 引用处理器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 引用处理器测试失败: {e}")
        return False

def test_processor_inheritance():
    """测试处理器继承关系"""
    try:
        from src.infrastructure.config.processor.base_processor import BaseConfigProcessor, IConfigProcessor
        from src.infrastructure.config.processor.environment_processor import EnvironmentProcessor
        from src.infrastructure.config.processor.reference_processor import ReferenceProcessor
        
        # 测试继承关系
        env_processor = EnvironmentProcessor()
        ref_processor = ReferenceProcessor()
        
        assert isinstance(env_processor, BaseConfigProcessor)
        assert isinstance(env_processor, IConfigProcessor)
        assert isinstance(ref_processor, BaseConfigProcessor)
        assert isinstance(ref_processor, IConfigProcessor)
        
        # 测试接口实现
        assert hasattr(env_processor, 'process')
        assert hasattr(env_processor, 'get_name')
        assert hasattr(ref_processor, 'process')
        assert hasattr(ref_processor, 'get_name')
        
        print("✅ 处理器继承关系测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 处理器继承关系测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("开始测试处理器基类统一化...")
    print("=" * 50)
    
    tests = [
        test_processor_imports,
        test_base_processor_functionality,
        test_environment_processor,
        test_reference_processor,
        test_processor_inheritance
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！处理器基类统一化成功。")
        return True
    else:
        print("⚠️  部分测试失败，需要进一步检查。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)