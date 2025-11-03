"""
Hash转换工具验证脚本

验证Hash转换工具的配置和功能是否正确。
"""

import sys
import os
from pathlib import Path
import yaml

def validate_hash_convert_config():
    """验证Hash转换工具配置文件"""
    print("开始验证Hash转换工具配置文件...")
    
    try:
        config_path = Path("configs/tools/hash_convert.yaml")
        if not config_path.exists():
            print(f"错误: 配置文件不存在: {config_path}")
            return False
            
        with open(config_path, 'r', encoding='utf-8') as f:
            hash_convert_config = yaml.safe_load(f)
        
        print(f"成功加载Hash转换工具配置")
        
        # 验证必需字段
        required_fields = ["name", "tool_type", "description", "function_path"]
        for field in required_fields:
            if field not in hash_convert_config:
                print(f"错误: 缺少必需字段 '{field}'")
                return False
        
        # 验证工具类型
        if hash_convert_config["tool_type"] != "builtin":
            print(f"错误: 工具类型应为 'builtin'，实际为 '{hash_convert_config['tool_type']}'")
            return False
        
        # 验证函数路径
        if hash_convert_config["function_path"] != "definition.tools.hash_convert:hash_convert":
            print(f"错误: 函数路径不正确，实际为 '{hash_convert_config['function_path']}'")
            return False
        
        # 验证参数Schema
        if "parameters_schema" not in hash_convert_config:
            print("错误: 缺少参数Schema")
            return False
            
        params_schema = hash_convert_config["parameters_schema"]
        if params_schema.get("type") != "object":
            print("错误: 参数Schema类型不正确")
            return False
            
        properties = params_schema.get("properties", {})
        if "text" not in properties:
            print("错误: 参数Schema缺少必需参数 'text'")
            return False
            
        # 验证必需参数列表
        required_params = params_schema.get("required", [])
        if "text" not in required_params:
            print("错误: 参数Schema中 'text' 未标记为必需参数")
            return False
        
        print("✓ Hash转换工具配置文件验证通过")
        return True
        
    except Exception as e:
        print(f"配置文件验证过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hash_convert_tool_functionality():
    """测试Hash转换工具功能"""
    print("\n开始测试Hash转换工具功能...")
    
    try:
        # 直接执行hash_convert.py文件来测试功能
        import subprocess
        import json
        
        # 运行hash_convert.py并捕获输出
        result = subprocess.run([
            sys.executable, 
            "definition/tools/hash_convert.py"
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("✓ Hash转换工具功能验证通过")
            return True
        else:
            print(f"✗ Hash转换工具功能验证失败: {result.stderr}")
            return False
        
    except Exception as e:
        print(f"功能测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Hash转换工具验证脚本")
    print("=" * 30)
    
    # 验证配置文件
    config_valid = validate_hash_convert_config()
    
    # 测试工具功能
    functionality_valid = test_hash_convert_tool_functionality()
    
    print("\n" + "=" * 30)
    if config_valid and functionality_valid:
        print("✓ Hash转换工具验证通过")
        print("  - 配置文件验证通过")
        print("  - 功能验证通过")
    else:
        print("✗ Hash转换工具验证失败")
        if not config_valid:
            print("  - 配置文件验证失败")
        if not functionality_valid:
            print("  - 功能验证失败")