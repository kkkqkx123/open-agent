"""
Hash转换工具加载测试脚本

测试Hash转换工具是否可以被工具管理器正确加载。
"""

import sys
from pathlib import Path
import tempfile
import shutil

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_tool_loading():
    """测试工具加载"""
    print("开始测试Hash转换工具加载...")
    
    try:
        from src.infrastructure.test_container import TestContainer
        
        # 创建临时目录
        temp_dir = Path(tempfile.mkdtemp())
        print(f"创建临时目录: {temp_dir}")
        
        try:
            # 创建配置目录结构
            (temp_dir / 'configs' / 'tools').mkdir(parents=True, exist_ok=True)
            
            # 复制配置文件
            shutil.copy(
                'configs/tools/hash_convert.yaml', 
                temp_dir / 'configs' / 'tools' / 'hash_convert.yaml'
            )
            
            # 使用测试容器
            with TestContainer(temp_dir) as container:
                container.setup_basic_configs()
                
                # 获取工具管理器
                tool_manager = container.get_tool_manager()
                
                # 加载工具
                tools = tool_manager.load_tools()
                print(f"成功加载 {len(tools)} 个工具")
                
                # 查找hash_convert工具
                hash_convert_tool = None
                for tool in tools:
                    print(f"已加载工具: {tool.name}")
                    if tool.name == 'hash_convert':
                        hash_convert_tool = tool
                        break
                
                if hash_convert_tool:
                    print("✓ Hash转换工具加载成功")
                    print(f"  工具名称: {hash_convert_tool.name}")
                    print(f"  工具描述: {hash_convert_tool.description}")
                    print(f"  工具参数: {hash_convert_tool.parameters_schema}")
                    return True
                else:
                    print("✗ 未找到Hash转换工具")
                    return False
                    
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"工具加载测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Hash转换工具加载测试")
    print("=" * 30)
    
    success = test_tool_loading()
    
    print("\n" + "=" * 30)
    if success:
        print("✓ Hash转换工具加载测试通过")
    else:
        print("✗ Hash转换工具加载测试失败")