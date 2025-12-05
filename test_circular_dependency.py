#!/usr/bin/env python3
"""测试循环依赖是否已解决"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试所有绑定文件是否可以正常导入"""
    try:
        print("测试导入绑定文件...")
        
        # 测试第一优先级文件
        print("  导入 history_bindings.py...")
        from src.services.container.bindings.history_bindings import HistoryServiceBindings
        
        print("  导入 llm_bindings.py...")
        from src.services.container.bindings.llm_bindings import LLMServiceBindings
        
        # 测试第二优先级文件
        print("  导入 session_bindings.py...")
        from src.services.container.bindings.session_bindings import SessionServiceBindings
        
        print("  导入 thread_bindings.py...")
        from src.services.container.bindings.thread_bindings import ThreadServiceBindings
        
        # 测试第三优先级文件
        print("  导入 config_bindings.py...")
        from src.services.container.bindings.config_bindings import ConfigServiceBindings
        
        print("  导入 thread_checkpoint_bindings.py...")
        from src.services.container.bindings.thread_checkpoint_bindings import ThreadCheckpointServiceBindings
        
        # 测试第四优先级文件
        print("  导入 logger_bindings.py...")
        from src.services.container.bindings.logger_bindings import LoggerServiceBindings
        
        print("  导入 storage_bindings.py...")
        from src.services.container.bindings.storage_bindings import StorageServiceBindings
        
        print("✅ 所有绑定文件导入成功！")
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def test_interface_dependencies():
    """测试接口依赖是否正确"""
    try:
        print("\n测试接口依赖...")
        
        # 测试接口导入
        print("  导入历史相关接口...")
        from src.interfaces.history import IHistoryManager, ICostCalculator
        
        print("  导入LLM相关接口...")
        from src.interfaces.llm import ITokenConfigProvider, ITokenCostCalculator
        
        print("  导入会话相关接口...")
        from src.interfaces.sessions import ISessionService, ISessionRepository
        
        print("  导入线程相关接口...")
        from src.interfaces.threads import IThreadService, IThreadRepository
        
        print("  导入配置相关接口...")
        from src.interfaces.config.interfaces import IConfigValidator
        
        print("  导入日志相关接口...")
        from src.interfaces.logger import ILogger
        
        print("✅ 所有接口导入成功！")
        return True
        
    except ImportError as e:
        print(f"❌ 接口导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def main():
    """主测试函数"""
    print("🔍 开始验证循环依赖重构结果...\n")
    
    # 测试导入
    imports_ok = test_imports()
    
    # 测试接口依赖
    interfaces_ok = test_interface_dependencies()
    
    # 总结
    print("\n" + "="*50)
    if imports_ok and interfaces_ok:
        print("🎉 循环依赖重构验证成功！")
        print("   - 所有绑定文件可以正常导入")
        print("   - 接口依赖模式工作正常")
        print("   - 循环依赖问题已解决")
    else:
        print("❌ 循环依赖重构验证失败")
        print("   - 存在导入或依赖问题")
    
    return imports_ok and interfaces_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)