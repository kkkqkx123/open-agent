"""组装系统使用示例

演示如何使用新的组件组装器和应用启动器。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.bootstrap import bootstrap_application


def main():
    """主函数"""
    print("=== 组装系统使用示例 ===")
    
    try:
        # 使用便捷函数启动应用
        container = bootstrap_application("configs/application.yaml")
        
        print("✅ 应用启动成功！")
        print(f"📦 当前环境: {container.get_environment()}")
        
        # 获取一些服务
        from src.infrastructure.config_loader import IConfigLoader
        
        try:
            config_loader = container.get(IConfigLoader)
            print(f"📋 配置加载器: {type(config_loader).__name__}")
        except Exception as e:
            print(f"⚠️  获取配置加载器失败: {e}")
        
        # 显示依赖分析
        if hasattr(container, 'analyze_dependencies'):
            analysis = container.analyze_dependencies()
            print(f"📊 依赖分析:")
            print(f"   - 总服务数: {analysis['total_services']}")
            print(f"   - 循环依赖: {len(analysis['circular_dependencies'])}")
            print(f"   - 根服务数: {len(analysis['root_services'])}")
        
        # 测试作用域功能
        if hasattr(container, 'scope'):
            print("\n🔄 测试作用域功能:")
            with container.scope() as scope_id:
                print(f"   创建作用域: {scope_id}")
                # 在作用域内可以获取作用域服务
        
        print("\n✅ 示例执行完成！")
        
    except Exception as e:
        print(f"❌ 示例执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()